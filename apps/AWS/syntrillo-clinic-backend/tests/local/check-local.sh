cd ~/SyntrilloClinic/apps/AWS/syntrillo-clinic-backend/lambda-functions

cd fitness-functions
cd ./check-connectivity-function/ # .env must be in this folder
python3 ./check_connectivity_function.py

cd -
cd ./check-behaviour-function/
python3 ./check_behaviour_function.py

cd -
cd ~/SyntrilloClinic/apps/AWS/syntrillo-clinic-backend
# DOES NOT WORK for the moment, because python modules are not in the lambda (they are on efs remotely)
# sam build --template cdk.out/SyntrilloClinicBackendStack.template.json
# sam local invoke --template cdk.out/SyntrilloClinicBackendStack.template.json IFrameGeneratorFunction |jq .
# cdk synth # this will take lambda code modification into account
# sam local start-api --template cdk.out/SyntrilloClinicBackendStack.template.json
