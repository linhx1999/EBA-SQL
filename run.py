# -*- coding: utf-8 -*-
from core.utils import *
from core.chat_manager import ChatManager
from core.utils import get_gold_columns
from core.const import SYSTEM_NAME
from tqdm import tqdm
import time
import argparse
import sys
import os
import json
from core import cost_log
import multiprocessing
from concurrent.futures import ProcessPoolExecutor, as_completed


_worker_manager = None


def _init_worker(manager_kwargs: dict, init_lock) -> None:
    global _worker_manager
    manager_kwargs = dict(manager_kwargs)
    cost_log.configure(*manager_kwargs.pop("_cost_context", (None, None)))
    log_path = manager_kwargs["log_path"] or "run.log"
    # Both run.log and api_trace.json must be isolated per process.
    manager_kwargs["log_path"] = os.path.join(
        os.path.dirname(log_path), f"worker_{os.getpid()}", os.path.basename(log_path)
    )
    # Selector initialization may generate shared matching/summary caches.
    with init_lock:
        _worker_manager = ChatManager(**manager_kwargs)


def _process_message(user_message: dict, chat_manager=None) -> dict:
    if chat_manager is None:
        chat_manager = _worker_manager
    started = time.monotonic()
    record = cost_log.begin_question(user_message['idx'], user_message['db_id'])
    record['status'] = 'failed'
    try:
        chat_manager.start(user_message)
        record['status'] = 'success'
        for key in ("desc_str", "fk_str", "send_to"):
            user_message.pop(key, None)
    except Exception as e:
        record["exception_class"] = type(e).__name__
        print(f"Exception: {type(e).__name__}, sleep 20 seconds.", flush=True)
        time.sleep(20)
    finally:
        user_message['exec_time'] = time.monotonic() - started
        user_message['execution_id'] = record['execution_id']
        record['exec_time'] = user_message['exec_time']
        cost_log.append('question_costs.jsonl', record)
    return user_message


def _run_messages(messages, manager_kwargs: dict, workers: int):
    manager_kwargs = dict(manager_kwargs)
    manager_kwargs['_cost_context'] = (str(cost_log._directory) if cost_log._directory else None, cost_log._session_id)
    if workers == 1:
        cost_log.configure(*manager_kwargs.pop('_cost_context'))
        chat_manager = ChatManager(**manager_kwargs)
        for message in messages:
            yield _process_message(message, chat_manager)
    else:
        context = multiprocessing.get_context("spawn")
        with ProcessPoolExecutor(
            max_workers=workers, mp_context=context, initializer=_init_worker,
            initargs=(manager_kwargs, context.Lock()),
        ) as executor:
            futures = [executor.submit(_process_message, message) for message in messages]
            for future in as_completed(futures):
                yield future.result()


def init_spider_message(idx: int, item: dict) -> dict:
    db_id, query, evidence, gt = item['db_id'], item['question'], str(""), item['query']
    difficulty = eval_hardness(item['sql'])
    user_message = {
        "idx": idx,
        "question_id": item.get("question_id", idx),
        "db_id": db_id,
        "query": query,
        "evidence": evidence,
        "extracted_schema": {},
        "ground_truth": gt,
        "difficulty": difficulty,
        "send_to": SYSTEM_NAME
    }
    return user_message


def init_bird_message(idx: int, item: dict, db_path: str=None, use_gold_schema: bool = False) -> dict:
    db_id, query, evidence, gt, difficulty = item['db_id'], \
                                             item['question'], \
                                             item['evidence'], \
                                             item.get('SQL', ''), \
                                             item.get('difficulty', 'simple')
    
    gold_schema_path = './data/bird/dev_gold_schema.json'
    gold_schema = {}
    all_gold_schema_dict = {}
    key = f"{db_id.strip()}\t{query.strip()}"
    if use_gold_schema:
        if os.path.exists(gold_schema_path):
            all_gold_schema_dict = load_json_file(gold_schema_path)
        if key in all_gold_schema_dict:
            gold_schema = all_gold_schema_dict[key]
        else:
            raise ValueError(f"Can't find gold schema for {key}")

    user_message = {
        "idx": idx,
        "question_id": item.get("question_id", idx),
        "db_id": db_id,
        "query": query,
        "evidence": evidence,
        "extracted_schema": gold_schema if gold_schema else {},
        "ground_truth": gt,
        "difficulty": difficulty,
        "send_to": SYSTEM_NAME
    }
    return user_message


@cost_log.log_run
def run_batch(dataset_name, input_file, output_file, db_path, tables_json_path, start_pos=0, log_file=None, dataset_mode='dev', use_gold_schema=False, without_selector=False, workers=1):
    if workers < 1:
        raise ValueError("workers must be at least 1")
    manager_kwargs = dict(data_path=db_path,
                               tables_json_path=tables_json_path,
                               log_path=log_file,
                               dataset_name=dataset_name,
                               dataset_path=input_file,
                               dataset_mode=dataset_mode,
                               model_name='gpt-3.5-turbo',
                               lazy=True,
                               without_selector=without_selector)
    batch = load_json_file(input_file)
    finished_ids = set()
    if os.path.exists(output_file):
        output_data_lst = load_jsonl_file(output_file)
        for o in output_data_lst:
            # only treat records with a predicted SQL as finished,
            # so failed items will be retried on re-run
            if 'pred' in o:
                finished_ids.add(o['idx'])

    unfinished_ids = [n for n in range(len(batch)) if n not in finished_ids and n >= start_pos]
    print(f"len(unfinished_data) = {len(unfinished_ids)}")


    for k, item in enumerate(batch):
        if 'question_id' not in item:
            item['question_id'] = k


    excluded_db_ids = []
    if dataset_mode == 'train':
        exclude_txt = './data/bird_train/excluded_db_ids.txt'
        excluded_db_ids = read_txt_file(exclude_txt)
    new_batch = []
    exclude_db_json_cnt = 0
    for k, item in enumerate(batch):
        # q_id = item['question_id']
        if k not in unfinished_ids:
            continue
        if dataset_mode == 'train':
            # skip excluded db_id
            if item['db_id'] in excluded_db_ids:
                exclude_db_json_cnt += 1
                continue
        # new_batch.append(item)
        new_batch.append((k, item))
    
    if exclude_db_json_cnt:
        print(f"excluded {exclude_db_json_cnt} excluded db json data")
    time.sleep(2)
    batch = new_batch

    count = 0
    run_time_start = time.time()
    out_dir = os.path.dirname(output_file)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    messages = []
    for idx, item in batch:
        if dataset_name == "spider":
            messages.append(init_spider_message(idx, item))
        elif dataset_name == "bird":
            messages.append(init_bird_message(idx, item, db_path=db_path, use_gold_schema=use_gold_schema))
    with open(output_file, 'a+', encoding='utf-8') as fp:
        for user_message in tqdm(_run_messages(messages, manager_kwargs, workers), total=len(messages)):
            # Only the parent writes results; completed items are flushed immediately.
            print(json.dumps(user_message, ensure_ascii=False), file=fp, flush=True)
        print(f"Result dump into {output_file}", file=sys.stdout, flush=True)

    out_dir = os.path.dirname(output_file)
    run_time_end = time.time()
    run_time = run_time_end - run_time_start
    print("运行时间: ", run_time, "秒")
    runTime = {"run_time": run_time}
    if dataset_name == "bird":
        # if dataset_mode == 'dev':
        #     run_time_path = "outputs_59.91/bird/dev/run_time.json"
        # else:
        #     run_time_path = "outputs_59.91/bird/test/run_time.json"
        run_time_path = f"{out_dir}/run_time.json"
        directory = os.path.dirname(run_time_path)
        if not os.path.exists(directory):
            os.makedirs(directory)
        with open(run_time_path, "w") as file:
            json.dump(runTime, file, indent=4)
    

    if dataset_name == "bird":
        evaluation_file_path = f"{out_dir}/predict_{dataset_mode}.json"
        with open(evaluation_file_path, 'w', encoding='utf8') as fout:
            output_json_list = load_jsonl_file(output_file)
            output_json_list = sorted(output_json_list, key=lambda i: i['idx'])
            eval_dict = {}
            for o in output_json_list:
                pred_sql = o.get('pred', '').strip()
                pred_sql = replace_multiple_spaces(pred_sql)
                sql_and_db_str = pred_sql + '\t' + '----- bird -----' + '\t' + o['db_id']
                eval_dict[str(o['idx'])] = sql_and_db_str
            json.dump(eval_dict, fp=fout, ensure_ascii=False, indent=4)
            print(f"BIRD format file dump into {evaluation_file_path}")

    elif dataset_name == "spider":
        evaluation_file_path = f"{out_dir}/pred_{dataset_mode}.sql"
        spider_sql_lst = []
        output_json_lst = sorted(load_jsonl_file(output_file), key=lambda item: item['idx'])
        for output_json in output_json_lst:
            if output_json.get('pred', 666) != 666:
                pred_sql = output_json['pred']
                pred_sql = replace_multiple_spaces(pred_sql)
            else: pred_sql = "SELECT SQL ERROR"
            spider_sql_lst.append(pred_sql.strip() + '\n')
        save_file(evaluation_file_path, spider_sql_lst)
        print(f"Spider format file dump into {evaluation_file_path}")
    else:
        raise NotImplementedError


def check_all_paths(args):

    if not os.path.exists(args.input_file):
        raise FileNotFoundError(f"Input file {args.input_file} not found")
    if not os.path.exists(args.db_path):
        raise FileNotFoundError(f"Database path {args.db_path} not found")
    if not os.path.exists(args.tables_json_path):
        raise FileNotFoundError(f"Tables json path {args.tables_json_path} not found")


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('--dataset_name', type=str, default='spider', choices=['spider', 'bird'], help='dataset name')
    parser.add_argument('--dataset_mode', type=str, default='dev', choices=['train', 'dev', 'test'], help='dataset mode')
    parser.add_argument('--input_file', type=str, required=True, help='path to dataset input')
    parser.add_argument('--db_path', type=str, required=True, help='path to databases in dataset')
    parser.add_argument('--tables_json_path', type=str, default=None, help='path to tables.json')
    parser.add_argument('--output_file', type=str, required=True, help='path to predicted output')
    parser.add_argument('--log_file', type=str, default='', help='path to log file if needed')
    parser.add_argument('--start_pos', type=int, default=0, help='start position of a batch')
    parser.add_argument('--use_gold_schema', action='store_true', default=False)
    parser.add_argument('--without_selector', action='store_true', default=False)
    parser.add_argument('--workers', type=int, default=1, help='number of parallel worker processes (default: 1)')
    args = parser.parse_args()
    if args.workers < 1:
        parser.error('--workers must be at least 1')
    for key, value in vars(args).items():
        print(f"{key}: {value}")

    check_all_paths(args)

    args_json_str = json.dumps(vars(args), indent=2, ensure_ascii=False)
    print(f"args:\n{args_json_str}")
    time.sleep(3)

    run_batch(
        dataset_name=args.dataset_name,
        dataset_mode=args.dataset_mode,
        input_file=args.input_file,
        output_file=args.output_file,
        db_path=args.db_path,
        tables_json_path=args.tables_json_path,
        log_file=args.log_file,
        start_pos=args.start_pos,
        use_gold_schema=args.use_gold_schema,
        without_selector=args.without_selector,
        workers=args.workers
    )
