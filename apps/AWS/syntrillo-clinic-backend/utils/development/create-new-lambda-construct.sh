cd ../..

if [ "$1" == "" ] || [ "$2" == "" ]; then  
    echo
    echo "usage: $0 <new_construct_name> model=<model_category/model_name>"
    echo
    echo "example: $0 heart_rate_analysis_function_construct.py model=tasks/blood_pressure_analysis_function_construct.py"
    echo
    echo "!!! Please respect naming conventions. Be aware of undescores (_) or hyphen ('-') in names"
    echo
    exit
fi

model_category=$(echo $2 | cut -d'=' -f2 | cut -d'/' -f1) # e.g. tasks
model_name=$(echo $2 | cut -d'=' -f2 | cut -d'/' -f2) # e.g. blood_pressure_analysis_function_construct.py

model_base_name=$(echo $model_name | cut -d'.' -f1) # e.g. blood_pressure_analysis_function_construct
model_construct_name=$(echo $model_base_name | sed 's/_function_construct//') # e.g. blood_pressure_analysis
model_lambda_function_folder_prefix=$(echo $model_construct_name | tr '_' '-') # e.g. blood-pressure-analysis
model_construct_name_camel_case=$(echo $model_construct_name | sed 's/^\([a-z]\)/\U\1/' | sed 's/_\([a-z]\)/\U\1/g') # e.g. BloodPressureAnalysis

new_construct_file=$1 # e.g. heart_rate_analysis_workflow_construct.py
new_construct_base_name=$(echo $new_construct_file | cut -d'.' -f1) # e.g. heart_rate_analysis_function_construct
new_construct_name=$(echo $new_construct_base_name | sed 's/_function_construct//')  # e.g. heart_rate_analysis
new_construct_lambda_function_folder_prefix=$(echo $new_construct_name | tr '_' '-') # e.g. heart-rate-analysis
new_construct_name_camel_case=$(echo $new_construct_name | sed 's/^\([a-z]\)/\U\1/' | sed 's/_\([a-z]\)/\U\1/g') # e.g. HeartRateAnalysis

cd syntrillo_clinic_backend/constructs
cp $model_category/$model_name $model_category/$new_construct_file
sed -i "s/$model_construct_name_camel_case/$new_construct_name_camel_case/g" $model_category/$new_construct_file
sed -i "s/$model_lambda_function_folder_prefix/$new_construct_lambda_function_folder_prefix/g" $model_category/$new_construct_file
cd - > /dev/null

echo "-----"
echo "Now add the import below to the 'FUNCTION CONSTRUCTS' section in [../../syntrillo_clinic_backend/substacks/task_scheduling_stack.py]"
echo
echo "from syntrillo_clinic_backend.constructs.$model_category.$new_construct_base_name import $new_construct_name_camel_case"
echo
echo "-----"
