if [ "$1" == "" -o "$2" == "" ]; then
    echo "usage: $0 asset_1  asset_2"
    exit
fi

arg_1=$(basename "$1" ".zip")
arg_2=$(basename "$2")

PROFILE="--profile syntrillo-clinic-staging-deployment"
if [ -n "$CODEBUILD_BUILD_ID" ]; then
    PROFILE=""
fi

REMOTE_CODE_URL=$(aws $PROFILE lambda get-function --function-name $arg_2 --query 'Code.Location' --output text)

if [ -d "/tmp/remote_code" ]; then
    rm -r /tmp/remote_code
fi

if [ -f "/tmp/remote_code.zip" ]; then
    rm /tmp/remote_code.zip
fi

curl -L -o /tmp/remote_code.zip "$REMOTE_CODE_URL"
unzip -q -o /tmp/remote_code.zip -d /tmp/remote_code

asset_1="../../cdk.out/asset.$arg_1"
asset_2="/tmp/remote_code"

echo $asset_1 $asset_2

diff -r $asset_1 $asset_2

rm -r /tmp/remote_code
rm /tmp/remote_code.zip
