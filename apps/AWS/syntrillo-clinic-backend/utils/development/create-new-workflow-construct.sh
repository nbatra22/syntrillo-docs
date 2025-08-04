#!/bin/bash

cd ../..

if [ "$1" == "" ] || [ "$2" == "" ]; then  
    echo
    echo "usage: $0 <new_construct_name> model=<model_category/model_name>"
    echo
    echo "example: $0 heart_rate_analysis_workflow_construct.py model=workflows/blood_pressure_analysis_workflow_construct.py"
    echo
    echo "!!! Please respect naming conventions. Be aware of undescores (_) or hyphen ('-') in names"
    echo
    exit
fi

model_category=$(echo $2 | cut -d'=' -f2 | cut -d'/' -f1) # e.g. workflows
model_name=$(echo $2 | cut -d'=' -f2 | cut -d'/' -f2) # e.g. blood_pressure_analysis_workflow_construct.py

model_base_name=$(echo $model_name | cut -d'.' -f1) # e.g. blood_pressure_analysis_workflow_construct
model_construct_name=$(echo $model_base_name | sed 's/_workflow_construct//') # e.g. blood_pressure_analysis
model_construct_name_camel_case=$(echo $model_construct_name | sed 's/^\([a-z]\)/\U\1/' | sed 's/_\([a-z]\)/\U\1/g') # e.g BloodPressureAnalysis
model_construct_name_capital=$(echo $model_construct_name | tr '_' ' ' | tr '[:lower:]' '[:upper:]') # e.g. BLOOD PRESSURE ANALYSIS

new_construct_file=$1 # e.g. heart_rate_analysis_workflow_construct.py
new_construct_base_name=$(echo $new_construct_file | cut -d'.' -f1) # e.g. heart_rate_analysis_workflow_construct
new_construct_name=$(echo $new_construct_base_name | sed 's/_workflow_construct//') # e.g. heart_rate_analysis
new_construct_name_camel_case=$(echo $new_construct_name | sed 's/^\([a-z]\)/\U\1/' | sed 's/_\([a-z]\)/\U\1/g') # e.g. HeartRateAnalysis
new_construct_name_capital=$(echo $new_construct_name | tr '_' ' ' | tr '[:lower:]' '[:upper:]') # e.g. HEART RATE ANALYSIS

cd syntrillo_clinic_backend/constructs
cp $model_category/$model_name $model_category/$new_construct_file
sed -i "s/$model_construct_name_camel_case/$new_construct_name_camel_case/g" $model_category/$new_construct_file
cd - > /dev/null

echo "-----"
echo "# Now add this import below in the "WORKFLOW CONSTRUCTS" section in [../../syntrillo_clinic_backend/substacks/task_scheduling_stack.py]"
echo "..."
echo "from syntrillo_clinic_backend.constructs.$model_category.$new_construct_base_name import ${new_construct_name_camel_case}WorkFlow"
echo "..."

echo "# AND this code at the end of in the 'WORKFLOW CONSTRUCTS' section in [../../syntrillo_clinic_backend/substacks/task_scheduling_stack.py]"
echo "..."
echo """
        # ---------------------------------------------------------------------
        # BLOOD PRESSURE ANALYSIS
        # ---------------------------------------------------------------------

        if self.aws_environment == \"staging\" or self.aws_environment == \"sandbox\" :
            self.blood_pressure_analysis = BloodPressureAnalysis(
                self, \"BloodPressureAnalysis\",
                aws_environment=self.aws_environment,
                network=self.network,
                database=self.database,
                storage=self.storage,
                secrets=self.secrets,
            )

            self.blood_pressure_analysis_worflow = BloodPressureAnalysisWorkFlow(
                self, \"BloodPressureAnalysisWorkFlow\",
                lambda_function=self.blood_pressure_analysis.function,
            )
""" \
    | sed "s/$model_construct_name_camel_case/$new_construct_name_camel_case/g" \
    | sed "s/$model_construct_name/$new_construct_name/g" \
    | sed "s/$model_construct_name_capital/$new_construct_name_capital/g"

echo "..."
echo "-----"
