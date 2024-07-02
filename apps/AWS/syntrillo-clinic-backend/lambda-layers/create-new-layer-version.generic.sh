# ------------------------------------------------------------------------------
# !!! IMPORTANT !!!
# ------------------------------------------------------------------------------
# This script is reference by a symlink in each folder of each layer
# it can not be executed at the lambda-layers root

# This script will be executed manually on demand

# - Each time requirements.txt is changed this sctipt 
# must be re-executed before a cdk deploy

# - Execution should be done on an Amazon Linux 2023 O.S., 
# otherwise the AWS Lambda service may not find the right dependency packages

# - Dependencies will be ignored in the .gitignore file 
# (this will drastically reduce the repository storage volume)

# - If you clone the repository for the first time and you want 
# to see the dependency packages, you have to execute that script
# ------------------------------------------------------------------------------

BASE_DIR=$(dirname "$0");
BASE_DIRE_NAME=$(basename "$BASE_DIR");

LAYER_NAME=$BASE_DIRE_NAME

echo "----------------------------------"
echo "$> INSTALL $LAYER_NAME PACKAGES LOCALLY "
echo "----------------------------------"
PACKAGE_FOLDER="python/lib/python3.10/site-packages"
rm -rf $PACKAGE_FOLDER
mkdir -p $PACKAGE_FOLDER
pip install -r requirements.txt --target $PACKAGE_FOLDER

echo "-----------------------------"
echo "$> ZIP LAYER PACKAGES        "
echo "-----------------------------"
rm /tmp/$LAYER_NAME/*.zip
zip -r /tmp/$LAYER_NAME.zip python/lib/python3.10/site-packages -x "**/__pycache__/*"
PACKAGE_SIZE=$(du -sh /tmp/$LAYER_NAME.zip)

echo "-------------------------------"
echo "$> DEPLOY NEW LAYER VERSION    "
echo "$> LAYER NAME: $LAYER_NAME     "
echo "$> PACKAGE SIZE: $PACKAGE_SIZE "
echo "-------------------------------"
aws lambda publish-layer-version \
    --layer-name $LAYER_NAME \
    --zip-file fileb:///tmp/$LAYER_NAME.zip \
    --compatible-runtimes python3.10