cd ~/SyntrilloClinic/apps/AWS/syntrillo-clinic-backend
cdk diff --profile syntrillo-clinic-staging --context 'environment=staging' $@
