#!/usr/bin/env bash
set -euo pipefail

export OPENAI_API_TYPE="open_ai"

# export OPENAI_API_BASE="https://llm-80oiqtb4br9yy56x.cn-beijing.maas.aliyuncs.com/compatible-mode/v1"
# export OPENAI_API_KEY="EMPTY"
# export MODEL_NAME="qwen3.6-35b-a3b"

export OPENAI_API_BASE="http://127.0.0.1:8003/v1"
export OPENAI_API_KEY="EMPTY"
# export MODEL_NAME="Qwen3.6-35B-A3B"
export MODEL_NAME="Qwen2.5-Coder-7B-Instruct"
# export MODEL_NAME="Ministral-3-14B-Reasoning-2512"

RUN_ID="cost_run_1"

DATA_ROOT="../SAGE-SQL/datasets/bird/dev"
OUTPUT_DIR="outputs/ebasql_bird_dev_${MODEL_NAME}_${RUN_ID}"
OUTPUT_FILE="${OUTPUT_DIR}/ebasql_bird_dev_${MODEL_NAME}_${RUN_ID}.jsonl"
LOG_FILE="${OUTPUT_DIR}/run.log"
WORKERS=8


cd "$(dirname "${BASH_SOURCE[0]}")"
# Override worker count with --workers 4.
python run.py \
    --workers "${WORKERS}" \
    --dataset_name bird \
    --dataset_mode dev \
    --input_file "${DATA_ROOT}/dev.json" \
    --db_path "${DATA_ROOT}/dev_databases" \
    --tables_json_path "${DATA_ROOT}/dev_tables.json" \
    --output_file "${OUTPUT_FILE}" \
    --log_file "${LOG_FILE}" \
    "$@"
