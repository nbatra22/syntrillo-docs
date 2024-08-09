#!/bin/bash --login

# Activate the Python environment
source /home/olivier/projects/Syntrillo/python_environments/p3.9_Syntrillo_Clinic_v7/bin/activate

cd /home/olivier/projects/Syntrillo/Syntrillo_Clinic/apps/AWS/syntrillo-clinic-backend/utils/bastion

# ssm-start.sh <environment> <session-type>
# environments: sandbox, staging
# session-types: session, ssh-tunnel, mysql-tunnel

./ssm-start.sh staging mysql-tunnel

