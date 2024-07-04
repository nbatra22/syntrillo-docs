cd ../../../syntrillo-clinic-backend/lambda-functions/fitness-functions
cd ./check-connectivity-function/
# .env must be in this folder
python3 ./check_connectivity_function.py

cd -
cd ../../../syntrillo-clinic-backend
# sam build --template cdk.out/SyntrilloClinicBackendStack.template.json
# sam local invoke --template cdk.out/SyntrilloClinicBackendStack.template.json CheckConnectivityFunction |jq .
# sam local start-api --template cdk.out/SyntrilloClinicBackendStack.template.json
