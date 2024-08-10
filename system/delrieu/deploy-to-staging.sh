#!/bin/bash --login

# Activate the Python environment
source /home/olivier/projects/Syntrillo/python_environments/p3.9_Syntrillo_Clinic_v7/bin/activate

cd /home/olivier/projects/Syntrillo/Syntrillo_Clinic/apps/AWS/syntrillo-clinic-backend/utils/deployments

./cdk-deploy-to-staging.sh \
    SyntrilloClinicBackendStack/ServersStack

echo "Waiting for the servers to be up and running ..."
curl --max-time 60 https://api.staging.syntrillo-clinic-backend.com/iframe_healthie_provider_tab > /dev/null 2>&1
sleep 5
curl --max-time 60 https://api.staging.syntrillo-clinic-backend.com/iframe_healthie_provider_tab > /dev/null 2>&1

echo "Deployed to staging"



