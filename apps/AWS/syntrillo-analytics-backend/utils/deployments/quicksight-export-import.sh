# AWS_ACCOUNT_ID='021891579520' # Staging
AWS_ACCOUNT_ID='381491864638' # Prod

AWS_REGION='us-east-1'
AWS_PROFILE='syntrillo-clinic-prod'
# AWS_PROFILE='syntrillo-clinic-staging'
ANALYSIS_ID='syntrillo-billing-report'
NAME="SyntrilloBillingReport"
USER_ROLE='SyntrilloClinicStagingUserRole'
USER_NAME='olemaitre'

# aws quicksight list-users --profile $AWS_PROFILE --aws-account-id $AWS_ACCOUNT_ID --namespace "default" --region us-east-1

# aws quicksight delete-data-set --aws-account-id $AWS_ACCOUNT_ID --data-set-id 'a64fa2ad-ea57-4fe9-9242-1d8271b73ebc' --profile $AWS_PROFILE
# aws quicksight list-data-sets --profile $AWS_PROFILE --aws-account-id $AWS_ACCOUNT_ID

aws quicksight delete-analysis --profile $AWS_PROFILE --aws-account-id  $AWS_ACCOUNT_ID --analysis-id $ANALYSIS_ID --region $AWS_REGION
# aws quicksight list-analyses --profile $AWS_PROFILE --aws-account-id $AWS_ACCOUNT_ID # --query 'AnalysisSummaryList[].DataSetArns[]'

# exit

# aws quicksight list-analyses  --aws-account-id $AWS_ACCOUNT_ID  --region $AWS_REGION
# aws quicksight --profile syntrillo-clinic-staging describe-analysis-definition     --aws-account-id $AWS_ACCOUNT_ID    --analysis-id ??? --region $AWS_REGION --query "Definition" > analysis_definition.json

aws quicksight create-analysis  --profile $AWS_PROFILE --aws-account-id $AWS_ACCOUNT_ID --analysis-id $ANALYSIS_ID  --name $NAME  --definition file://quicksight-dashboard-definition.json
# aws quicksight update-analysis  --profile $AWS_PROFILE --aws-account-id $AWS_ACCOUNT_ID --analysis-id $ANALYSIS_ID  --name $NAME  --definition file://quicksight-dashboard-definition.json

# IF ANALYSIS CREATION FAILS
aws quicksight describe-analysis --aws-account-id $AWS_ACCOUNT_ID --analysis-id $ANALYSIS_ID --profile $AWS_PROFILE


# exit

aws quicksight update-analysis-permissions  --profile $AWS_PROFILE   --aws-account-id $AWS_ACCOUNT_ID --analysis-id $ANALYSIS_ID --region $AWS_REGION --grant-permissions "[{\"Principal\": \"arn:aws:quicksight:us-east-1:$AWS_ACCOUNT_ID:namespace/default\", \"Actions\": [\"quicksight:DescribeAnalysis\",\"quicksight:QueryAnalysis\"]}]"
# aws quicksight update-analysis-permissions  --profile $AWS_PROFILE   --aws-account-id $AWS_ACCOUNT_ID --analysis-id syntrillo-billing-report-2 --region $AWS_REGION --grant-permissions "[{\"Principal\": \"arn:aws:quicksight:us-east-1:$AWS_ACCOUNT_ID:user/default/$USER_ROLE/$USER_NAME\", \"Actions\": [\"quicksight:RestoreAnalysis\", \"quicksight:UpdateAnalysisPermissions\", \"quicksight:DeleteAnalysis\", \"quicksight:QueryAnalysis\", \"quicksight:DescribeAnalysisPermissions\", \"quicksight:DescribeAnalysis\", \"quicksight:UpdateAnalysis\"]}]"

# aws quicksight describe-analysis-permissions  --profile $AWS_PROFILE   --aws-account-id $AWS_ACCOUNT_ID --analysis-id $ANALYSIS_ID --region $AWS_REGION

# exit