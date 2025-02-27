#!/bin/bash

if [ "$1" == "" ]; then
  echo "Usage: $0 <environment> [stacks]"
  echo "Environments: sandbox, staging, prod"
  exit
fi

ENVIRONMENT=$1

./cdk-diff-with-$ENVIRONMENT.sh 2>&1  |tee /tmp/cdk-diff.txt

./list-functions-from-cdk-diff.sh | tee /tmp/functions.txt
./list-assets-from-cdk-diff.sh | tee /tmp/assets.txt

asset_row_number=1
functions=$(cat /tmp/functions.txt)

if [ "$functions" == "" ]; then
  echo "No changes detected"
  exit
fi

for function_name in $functions; do
  asset_ref=$(sed -n "${asset_row_number}p" /tmp/assets.txt)
  asset_folder="asset.$asset_ref"
  echo $asset_folder

  echo "-------------------------------"
  echo "COMPARING..."
  echo "function name: $function_name"
  echo "asset folder: $asset_folder"
  echo "-------------------------------"

  ./diff-asset-function.sh $asset_ref $function_name || true

  let asset_row_number=$asset_row_number+1
done
cd -