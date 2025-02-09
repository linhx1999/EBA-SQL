@echo off
chcp 65001

@REM #################### Spider dev 【run】count=1034 #########
@REM Generate SQL on Spider dev dataset
python ./run.py --dataset_name "spider" ^
   --dataset_mode="dev" ^
   --input_file "./data/spider/dev.json" ^
   --db_path "./data/spider/database" ^
   --tables_json_path "./data/spider/tables.json" ^
   --output_file "./outputs/spider/output_spider_dev.json" ^
   --log_file "./outputs/spider/log_dev.txt"

@REM Generate SQL on Spider test dataset
@REM   python ./run.py --dataset_name "spider" ^
@REM     --dataset_mode="test" ^
@REM     --input_file "./data/spider/test.json" ^
@REM     --db_path "./data/spider/test_database" ^
@REM     --tables_json_path "./data/spider/test_tables.json" ^
@REM     --output_file "./outputs/spider/output_spider_test.json" ^
@REM     --log_file "./outputs/spider/log_test.txt"

@REM #################### Spider dev 【evaluation】EX and EM count=1034 #########
@REM python ./evaluation/evaluation_spider.py ^
@REM    --gold "./data/spider/dev_gold.sql" ^
@REM    --db "./data/spider/database" ^
@REM    --table "./data/spider/tables.json" ^
@REM    --pred "./outputs/spider/pred_dev.sql" ^
@REM    --etype "exec" ^
@REM    --plug_value ^
@REM    --keep_distinct ^
@REM    --progress_bar_for_each_datapoint

@REM  python ./evaluation/evaluation_spider.py ^
@REM     --gold "./data/spider/test_gold.sql" ^
@REM     --db "./data/spider/test_database" ^
@REM     --table "./data/spider/test_tables.json" ^
@REM     --pred "./outputs/spider/pred_test.sql" ^
@REM     --etype "exec" ^
@REM     --plug_value ^
@REM     --keep_distinct ^
@REM     --progress_bar_for_each_datapoint


echo "Done!"