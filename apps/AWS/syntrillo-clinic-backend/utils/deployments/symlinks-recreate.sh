#!/bin/bash

create_symlinks() {
    local dir=$1
    
    cd "$dir"
    
    # Array of files/dirs to process
    local items="routes static syntrillo templates api.py"    

    # Process each item
    for item in "${items[@]}"; do
        if [ -e "$item" ]; then
            mv "$item" "${item}.tmp"
            ln -s "$(cat ${item}.tmp)" "$item"
            rm "${item}.tmp"
        fi
    done
    
    ls -l
    cd -
}

create_symlinks "../../lambda-functions/iframe-generator-function/" "routes static syntrillo templates api.py flask_app.py"
create_symlinks "../../lambda-functions/message-endpoint-function/" "routes static syntrillo templates api.py"
create_symlinks "../../lambda-functions/blood-pressure-notification-function/" "syntrillo"
create_symlinks "../../../../PythonAnywhere/website/static/healthie/documents/" "questionnaire_template_latest.xlsx"