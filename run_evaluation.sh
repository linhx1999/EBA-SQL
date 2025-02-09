db_root_path='./data/bird/dev/dev_databases/'
data_mode='dev'
diff_json_path='./data/bird/dev/dev.json'
predicted_sql_path_kg='./outputs_59.91/bird/dev/'
ground_truth_path='./data/bird/dev/'
num_cpus=12
meta_time_out=30.0
mode_gt='gt'
mode_predict='gpt'

#db_root_path='./data/bird/test/test_databases/'
#data_mode='test'
#diff_json_path='./data/bird/test/test.json'
#predicted_sql_path_kg='./outputs_59.91/bird/test/'
#ground_truth_path='./data/bird/test/'
#num_cpus=12
#meta_time_out=30.0
#mode_gt="gt"
#mode_predict="gpt"

echo '''starting to compare with knowledge for ex and ves'''
python3 -u ./evaluation/evaluation.py --db_root_path ${db_root_path} --predicted_sql_path ${predicted_sql_path_kg} --data_mode ${data_mode} \
--ground_truth_path ${ground_truth_path} --num_cpus ${num_cpus} --mode_gt ${mode_gt} --mode_predict ${mode_predict} \
--diff_json_path ${diff_json_path} --meta_time_out ${meta_time_out} 
echo "Evaluate EX done!"
python3 -u ./evaluation/evaluation_ves.py --db_root_path ${db_root_path} --predicted_sql_path ${predicted_sql_path_kg} --data_mode ${data_mode} \
--ground_truth_path ${ground_truth_path} --num_cpus ${num_cpus} --mode_gt ${mode_gt} --mode_predict ${mode_predict} \
--diff_json_path ${diff_json_path} --meta_time_out ${meta_time_out}
echo "Evaluate VES done!"