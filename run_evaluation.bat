@echo off
chcp 65001

@REM  #################### BIRD dev 【run】count=1534 #########
 set db_root_path="./data/bird/dev/dev_databases/"
 set data_mode="dev"
 set diff_json_path="./data/bird/dev/dev.json"
 set predicted_sql_path_kg="./outputs/bird/dev/"
 set ground_truth_path="./data/bird/dev/"
 set num_cpus=12
 set meta_time_out=30.0
 set mode_gt="gt"
 set mode_predict="gpt"

@REM  #################### BIRD test 【run】count=1789 #########
@REM  set db_root_path="./data/bird/test/test_databases/"
@REM  set data_mode="test"
@REM  set diff_json_path="./data/bird/test/test.json"
@REM  set predicted_sql_path_kg="./outputs/bird/test/"
@REM  set ground_truth_path="./data/bird/test/"
@REM  set num_cpus=12
@REM  set meta_time_out=30.0
@REM  set mode_gt="gt"
@REM  set mode_predict="gpt"

@REM evaluate EX and VES
echo "starting to compare with knowledge for ex and ves"
python ./evaluation/evaluation.py --db_root_path %db_root_path% --predicted_sql_path %predicted_sql_path_kg% --data_mode %data_mode% ^
--ground_truth_path %ground_truth_path% --num_cpus %num_cpus% --mode_gt %mode_gt% --mode_predict %mode_predict% ^
--diff_json_path %diff_json_path% --meta_time_out %meta_time_out%
echo "Evaluate EX done!"
python ./evaluation/evaluation_ves.py --db_root_path %db_root_path% --predicted_sql_path %predicted_sql_path_kg% --data_mode %data_mode% ^
--ground_truth_path %ground_truth_path% --num_cpus %num_cpus% --mode_gt %mode_gt% --mode_predict %mode_predict% ^
--diff_json_path %diff_json_path% --meta_time_out %meta_time_out%
echo "Evaluate VES done!"

