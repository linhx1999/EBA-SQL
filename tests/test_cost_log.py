"""Offline generation telemetry regressions; no SDK or model endpoint required."""
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace, ModuleType
import unittest
from unittest.mock import patch
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import multiprocessing

from core import cost_log


def load_llm(create):
    config = ModuleType('core.api_config')
    config.os = os
    config.MODEL_NAME = 'fake-model'
    config.MAX_TOKENS = 100
    config.openai = SimpleNamespace(api_type='open_ai', ChatCompletion=SimpleNamespace(create=create))
    path = Path(__file__).resolve().parents[1] / 'core' / 'llm.py'
    spec = importlib.util.spec_from_file_location('cost_test_llm', path)
    module = importlib.util.module_from_spec(spec)
    with patch.dict(sys.modules, {'core.api_config': config, 'openai': config.openai}):
        spec.loader.exec_module(module)
    return module


def spawned_request(directory, index):
    cost_log.configure(directory, 'session')
    cost_log.begin_question(index, 'db')
    cost_log.begin_call({'send_to': 'Refiner'})
    cost_log.request(lambda **kwargs: {}, model='m', messages=[])


class CostLogTests(unittest.TestCase):
    def tearDown(self):
        cost_log._directory = None
        cost_log._session_id = None

    def test_retry_and_usage_are_preserved(self):
        calls = []
        def create(**kwargs):
            calls.append(kwargs)
            if len(calls) == 1:
                raise RuntimeError('SECRET')
            return {'choices': [{'message': {'content': 'SELECT 1'}, 'finish_reason': 'stop'}], 'usage': {'prompt_tokens': 5, 'completion_tokens': 2}}
        with tempfile.TemporaryDirectory() as directory:
            cost_log._directory = Path(directory)
            llm = load_llm(create)
            cost_log.begin_question(7, 'db')
            with patch.object(llm.time, 'sleep'):
                self.assertEqual(llm.safe_call_llm('p', send_to='Refiner'), 'SELECT 1')
            text = (Path(directory) / 'llm_attempts.jsonl').read_text()
            rows = list(map(json.loads, text.splitlines()))
            self.assertNotIn('SECRET', text)
            self.assertEqual([r['attempt'] for r in rows], [1, 2])
            self.assertEqual(rows[0]['call_id'], rows[1]['call_id'])
            self.assertIsNone(rows[0]['prompt_tokens'])
            self.assertEqual(rows[1]['prompt_tokens'], 5)
            self.assertEqual(rows[1]['stage'], 'Refiner')

    def test_truncated_response_usage_survives_parsing_failure(self):
        def create(**kwargs):
            return {'choices': [{'message': {'content': None}, 'finish_reason': 'length'}], 'usage': {'prompt_tokens': 5, 'completion_tokens': 100}}
        with tempfile.TemporaryDirectory() as directory:
            cost_log._directory = Path(directory)
            llm = load_llm(create)
            with self.assertRaises(AttributeError):
                llm.api_func('p')
            row = json.loads((Path(directory) / 'llm_attempts.jsonl').read_text())
            self.assertEqual(row['completion_tokens'], 100)
            self.assertEqual(row['finish_reason'], 'length')

    def test_missing_usage_does_not_retry_valid_response(self):
        def create(**kwargs):
            return {'choices': [{'message': {'content': 'SELECT 1'}}]}
        with tempfile.TemporaryDirectory() as directory:
            cost_log._directory = Path(directory)
            llm = load_llm(create)
            llm.init_log_path(str(Path(directory) / 'log.txt'))
            self.assertEqual(llm.safe_call_llm('p'), 'SELECT 1')
            row = json.loads((Path(directory) / 'llm_attempts.jsonl').read_text())
            self.assertIsNone(row['prompt_tokens'])

    def test_thread_context_isolation(self):
        with tempfile.TemporaryDirectory() as directory:
            cost_log._directory = Path(directory)
            def work(i):
                cost_log.begin_question(i, 'db')
                cost_log.begin_call({'send_to': str(i)})
                cost_log.request(lambda **kwargs: {}, model='m', messages=[])
            with ThreadPoolExecutor(max_workers=4) as pool:
                list(pool.map(work, range(40)))
            rows = list(map(json.loads, (Path(directory) / 'llm_attempts.jsonl').read_text().splitlines()))
            self.assertEqual({r['idx'] for r in rows}, set(range(40)))
            self.assertTrue(all(str(r['idx']) == r['stage'] for r in rows))

    def test_invocations_append_and_failures_finalize(self):
        @cost_log.log_run
        def run(input_file, output_file, num_workers=1):
            raise ValueError('failed setup')
        with tempfile.TemporaryDirectory() as directory:
            data = Path(directory) / 'data.json'
            data.write_text('[]')
            for _ in range(2):
                with self.assertRaises(ValueError):
                    run(str(data), str(Path(directory) / 'output.jsonl'))
            rows = list(map(json.loads, (Path(directory) / 'run_sessions.jsonl').read_text().splitlines()))
            self.assertEqual(len(rows), 2)
            self.assertNotEqual(rows[0]['session_id'], rows[1]['session_id'])
            self.assertEqual(rows[0]['status'], 'interrupted_or_failed')

    def test_spawned_workers_share_durable_log(self):
        with tempfile.TemporaryDirectory() as directory:
            with ProcessPoolExecutor(max_workers=3, mp_context=multiprocessing.get_context('spawn')) as pool:
                futures = [pool.submit(spawned_request, directory, i) for i in range(30)]
                for future in futures:
                    future.result()
            rows = list(map(json.loads, (Path(directory) / 'llm_attempts.jsonl').read_text().splitlines()))
            self.assertEqual({r['idx'] for r in rows}, set(range(30)))
            self.assertTrue(all(r['session_id'] == 'session' for r in rows))
