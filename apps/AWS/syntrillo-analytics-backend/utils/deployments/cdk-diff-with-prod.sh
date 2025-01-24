cd ~/SyntrilloClinic/apps/AWS/syntrillo-clinic-backend
cdk diff --profile syntrillo-clinic-prod-deployment --context environment='prod' $@ 
