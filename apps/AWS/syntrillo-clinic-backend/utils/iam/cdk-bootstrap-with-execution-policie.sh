# !!!! EXECUTE WITH ADMIN PERMISSIONS IN syntrillo-clinic-prod-deployment PROFILE
# !!!! OTHERWISE YOU MAY BE STUCK IN A CLOUDFORMATION STATE

echo "EXECUTE WITH ADMIN PERMISSIONS IN syntrillo-clinic-prod-deployment PROFILE and REMOVE EXIT LINE"
echo "N.B. Delete cdk bucket before first execution"
exit

cdk bootstrap aws://381491864638/us-east-1 --cloudformation-execution-policies 'arn:aws:iam::381491864638:policy/SyntrilloClinicBackendCdkCloudFormationExecutionPolicy','arn:aws:iam::aws:policy/ReadOnlyAccess' --profile syntrillo-clinic-prod-deployment
