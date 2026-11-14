"""Thread-safe request, question and invocation accounting without model calls."""
from __future__ import annotations

import fcntl
import functools
import hashlib
import inspect
import json
import os
from pathlib import Path
import threading
import time
import uuid

_local = threading.local()
_lock = threading.Lock()
_directory = None
_session_id = None


def append(name, record):
    if _directory is None:
        return
    with _lock, (_directory / name).open('a', encoding='utf-8') as stream:
        fcntl.flock(stream, fcntl.LOCK_EX)
        stream.write(json.dumps(record, ensure_ascii=False) + '\n')
        stream.flush()
        os.fsync(stream.fileno())


def begin_question(idx, db_id):
    _local.context = {'idx': idx, 'db_id': db_id, 'execution_id': uuid.uuid4().hex,
                      'session_id': _session_id}
    return dict(_local.context)


def begin_call(metadata):
    _local.call_id = uuid.uuid4().hex
    _local.attempt = 0
    _local.stage = metadata.get('send_to', 'unknown')


def request(create, **kwargs):
    _local.attempt = getattr(_local, 'attempt', 0) + 1
    record = dict(getattr(_local, 'context', {}), call_id=getattr(_local, 'call_id', None),
                  attempt=_local.attempt, stage=getattr(_local, 'stage', 'unknown'),
                  model=kwargs.get('model', kwargs.get('engine')), request_scope='sdk_invocation',
                  started_unix=time.time(), prompt_tokens=None, completion_tokens=None, reasoning_tokens=None,
                  prompt_sha256=hashlib.sha256(json.dumps(kwargs.get('messages'), sort_keys=True).encode()).hexdigest())
    started = time.monotonic()
    try:
        response = create(**kwargs)
        usage = response.get('usage') or {}
        choices = response.get('choices') or []
        record.update(status='success', response_received=True,
                      prompt_tokens=usage.get('prompt_tokens'), completion_tokens=usage.get('completion_tokens'),
                      reasoning_tokens=(usage.get('completion_tokens_details') or {}).get('reasoning_tokens'),
                      finish_reason=choices[0].get('finish_reason') if choices else None)
        return response
    except Exception as exc:
        record.update(status='failed', exception_class=type(exc).__name__)
        raise
    finally:
        record['elapsed_seconds'] = time.monotonic() - started
        append('llm_attempts.jsonl', record)


def log_run(function):
    @functools.wraps(function)
    def wrapped(*args, **kwargs):
        global _directory, _session_id
        params = inspect.signature(function).bind(*args, **kwargs)
        params.apply_defaults()
        directory = Path(params.arguments['output_file']).resolve().parent
        directory.mkdir(parents=True, exist_ok=True)
        with (directory / '.cost_run.lock').open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            _directory, _session_id = directory, uuid.uuid4().hex
            started = time.monotonic()
            record = {'session_id': _session_id, 'started_unix': time.time(),
                      'status': 'interrupted_or_failed', 'config': dict(params.arguments),
                      'model': os.environ.get('MODEL_NAME'), 'request_scope': 'sdk_invocation',
                      'sdk_internal_retries': 'not individually observed; retry policy unchanged'}
            source = Path(__file__).resolve().parents[1]
            record['code_sha256'] = {name: hashlib.sha256((source / name).read_bytes()).hexdigest()
                                     for name in ['run.py', 'core/llm.py', 'core/cost_log.py']}
            record['max_tokens'] = os.environ.get('MAX_TOKENS')
            record['temperature'] = float(os.environ.get('TEMPERATURE', '0'))
            record['input_sha256'] = hashlib.sha256(Path(params.arguments['input_file']).read_bytes()).hexdigest()
            try:
                return_value = function(*args, **kwargs)
                record['status'] = 'completed'
                return return_value
            finally:
                record['run_time'] = time.monotonic() - started
                record['scope'] = 'this invocation only, including setup and export'
                append('run_sessions.jsonl', record)
                for name, data in [('run_time.json', record), ('run_config.json', {k: v for k, v in record.items() if k not in ['run_time', 'status']})]:
                    tmp = directory / (name + '.tmp')
                    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2))
                    tmp.replace(directory / name)
                _directory, _session_id = None, None
    return wrapped


def configure(directory, session_id):
    global _directory, _session_id
    _directory = Path(directory) if directory else None
    _session_id = session_id
    _local.context = {'session_id': session_id, 'scope': 'worker_initialization'}
