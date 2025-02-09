#!/bin/bash

# #################### BIRD dev 【run】count=1534 #########
# Generate SQL on BIRD dev dataset
 python ./run.py --dataset_name="bird" \
    --dataset_mode="dev" \
    --input_file="./data/bird/dev/dev.json" \
    --db_path="./data/bird/dev/dev_databases/" \
    --tables_json_path "./data/bird/dev/dev_tables.json" \
    --output_file="./outputs/bird/dev/output_dev.json" \
    --log_file="./outputs/bird/dev/log_dev.txt"

# #################### BIRD test 【run】count=1789 #########
# Generate SQL on BIRD test dataset
# python ./run.py --dataset_name="bird" \
#    --dataset_mode="test" \
#    --input_file="./data/bird/test/test.json" \
#    --db_path="./data/bird/test/test_databases/" \
#    --tables_json_path "./data/bird/test/test_tables.json" \
#    --output_file="./outputs_59.91/bird/test/output_test.json" \
#    --log_file="./outputs_59.91/bird/test/log_test.txt"

# #################### BIRD dev 【evaluation】=1534, see run_evaluation.sh #########

# #################### BIRD test 【evaluation】=1789, see run_evaluation.sh #########


echo "Done!"