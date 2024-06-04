
# !!! WORK IN PROGRESS !!!

# Prequisites

If you do a first cdk deployment in an enviroment you must boostap the environement 
```
$> cdk bootstrap aws://[ACCOUNT_NUMBER]/us-east-1
```

If you want to test lambdas and apis locally, you should install AWS SAM (IF NOT INSTALLED YET)

source: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html

```
$> wget https://github.com/aws/aws-sam-cli/releases/latest/download/aws-sam-cli-linux-x86_64.zip
$> unzip aws-sam-cli-linux-x86_64.zip -d sam-installation
$> sudo ./sam-installation/install

$> sam --version # To test it worked
$> rm -r aws-sam-cli-linux-x86_64.zip sam-installation/ # To clean your folder
```

# How to deploy the CDK app

```
$> cdk deploy
```


# How to install lambda code dependencies at the lambda root

```
$> cd /path/to/your/lambda
$> pip install -r requirements.txt --target .
```

# How to install lambda code dependencies at the lambda layer

```
$> cd /path/to/your/lambda/layer
$> mkdir -p python/lib/python3.10/site-packages
$> cd python
$> pip install -r requirements.txt --target .
```

# How to test a lambda locally with AWS SAM (work in progress)

source: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-cdk-testing.html

```
$> cdk synth
$> sam local invoke -t ./cdk.out/SyntrilloClinicBackendStack.template.json IFrameGeneratorFunction
```

# How to build a cdk application from scratch

Install node.js > 14.15.0 IF NOT DONE YET
```
$> curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/master/install.sh | bash
```

```
$> nvm install --lts
```

Install the cdk IF NOT DONE YET

```
$> npm install -g aws-cdk
```

Then create the application IF NOT DONE YET
```
$> mkdir syntrillo-clinic-backend

$> cd syntrillo-clinic-backend/

$> cdk init app --language python

$> python3 -m pip install -r requirements.txt
```

Bootstrap the application IF NOT DONE YET:
```
$> cdk bootstrap aws://[ACCOUNT_NUMBER]/us-east-1
```

```
$> cdk deploy
```
