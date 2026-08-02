#!/usr/bin/env bash
set -euo pipefail

export OPENAI_API_TYPE="open_ai"
export OPENAI_API_BASE="http://127.0.0.1:8002/v1"
export OPENAI_API_KEY="EMPTY"
export MODEL_NAME="Qwen2.5-Coder-7B-Instruct"

DATA_ROOT="../datasets/spider"
OUTPUT_DIR="outputs/ebasql_spider_dev_${MODEL_NAME}"
OUTPUT_FILE="${OUTPUT_DIR}/ebasql_spider_dev_${MODEL_NAME}.jsonl"
LOG_FILE="${OUTPUT_DIR}/run.log"


python run.py \
    --dataset_name spider \
    --dataset_mode dev \
    --input_file "${DATA_ROOT}/dev.json" \
    --db_path "${DATA_ROOT}/database" \
    --tables_json_path "${DATA_ROOT}/tables.json" \
    --output_file "${OUTPUT_FILE}" \
    --log_file "${LOG_FILE}" \
    "$@"
