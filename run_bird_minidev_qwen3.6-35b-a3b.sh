#!/usr/bin/env bash
set -euo pipefail

export OPENAI_API_TYPE="open_ai"
export OPENAI_API_BASE="http://127.0.0.1:8004/v1"
export OPENAI_API_KEY="EMPTY"
export MODEL_NAME="Qwen3.6-35B-A3B"

DATA_ROOT="../datasets/bird/MINIDEV"
OUTPUT_DIR="outputs/ebasql_bird_minidev_${MODEL_NAME}"
OUTPUT_FILE="outputs/ebasql_bird_minidev_${MODEL_NAME}/ebasql_bird_minidev_${MODEL_NAME}.jsonl"
LOG_FILE="outputs/ebasql_bird_minidev_${MODEL_NAME}/run.log"


python run.py \
    --dataset_name bird \
    --dataset_mode dev \
    --input_file "${DATA_ROOT}/mini_dev_sqlite.json" \
    --db_path "${DATA_ROOT}/dev_databases" \
    --tables_json_path "${DATA_ROOT}/dev_tables.json" \
    --output_file "${OUTPUT_FILE}" \
    --log_file "${LOG_FILE}" \
    "$@"
