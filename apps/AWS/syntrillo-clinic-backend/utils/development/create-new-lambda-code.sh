#!/bin/bash

cd ../..

if [ "$1" == "" ] || [ "$2" == "" ]; then  
    echo
    echo "usage: $0 <new_function_name> model=<model_category/model_name>"
    echo
    echo "example: $0 heart-rate-analysis-function model=tasks/blood-pressure-analysis-function"
    echo
    echo "!!! Please respect naming conventions. Be aware of undescores (_) or hyphen ('-') in names"
    echo
    exit
fi

model_category=$(echo $2 | cut -d'=' -f2 | cut -d'/' -f1) # e.g. tasks
model_folder=$(echo $2 | cut -d'=' -f2 | cut -d'/' -f2) # e.g. blood_pressure-analysis-function

new_function_folder=$1 # e.g. heart-rate-analysis-function

cd lambda-functions
mkdir ./$model_category/$new_function_folder
cp -r ./$model_category/$model_folder/* ./$model_category/$new_function_folder
cd - > /dev/null