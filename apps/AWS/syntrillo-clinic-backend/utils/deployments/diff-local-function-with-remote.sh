if [ "$1" == "" -o "$2" == "" ]; then
    echo "usage: $0 function_name  function_folder"
    exit
fi

arg_1=$(basename "$1")
arg_2=$(basename "$2")

PROFILE="--profile syntrillo-clinic-staging"
if [ -n "$CODEBUILD_BUILD_ID" ]; then
    PROFILE=""
fi

REMOTE_CODE_URL=$(aws $PROFILE lambda get-function --function-name $arg_1 --query 'Code.Location' --output text)

if [ -d "/tmp/remote_code" ]; then
    rm -r /tmp/remote_code
fi

if [ -f "/tmp/remote_code.zip" ]; then
    rm /tmp/remote_code.zip
fi

curl -L -o /tmp/remote_code.zip "$REMOTE_CODE_URL"
unzip -q -o /tmp/remote_code.zip -d /tmp/remote_code

function_name="../../lambda-functions/$arg_2"
function_folder="/tmp/remote_code"

echo $function_name $function_folder

diff -r $function_name $function_folder