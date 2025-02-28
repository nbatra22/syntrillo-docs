cd ~/SyntrilloClinic/apps/AWS/syntrillo-analytics-backend
cdk diff --profile syntrillo-clinic-prod-deployment --context environment='prod' $@ 
