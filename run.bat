@echo off
chcp 65001


@REM #################### BIRD dev 【run】count=1534 #########
@REM Generate SQL on BIRD dev dataset
 python ./run.py --dataset_name="bird" ^
    --dataset_mode="dev" ^
    --input_file="./data/bird/dev/dev.json" ^
    --db_path="./data/bird/dev/dev_databases/" ^
    --tables_json_path "./data/bird/dev/dev_tables.json" ^
    --output_file="./outputs/bird/dev/output_dev.json" ^
    --log_file="./outputs/bird/dev/log_dev.txt"


@REM #################### BIRD test 【run】count=1789 #########
@REM  Generate SQL on BIRD test dataset
@REM  python ./run.py --dataset_name="bird" ^
@REM     --dataset_mode="test" ^
@REM     --input_file="./data/bird/test/test.json" ^
@REM     --db_path="./data/bird/test/test_databases/" ^
@REM     --tables_json_path "./data/bird/test/test_tables.json" ^
@REM     --output_file="./outputs/bird/test/output_test.json" ^
@REM     --log_file="./outputs/bird/test/log_test.txt"


@REM #################### BIRD dev 【evaluation】=1534, see run_evaluation.bat #########

@REM #################### BIRD test 【evaluation】=1789, see run_evaluation.bat #########


echo "Done!"