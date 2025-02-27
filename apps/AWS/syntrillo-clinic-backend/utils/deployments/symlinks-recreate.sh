#!/bin/bash

create_symlinks() {
    local dir=$1
    
    cd "$dir"
    
    echo "symlink rewrite => $dir ($2)"

    # Array of files/dirs to process
    local items=($2) 

    # Process each item
    for item in "${items[@]}"; do
        if [ -e "$item" ]; then
            if [ -n "$CODEBUILD_BUILD_ID" ]; then # only execute this in CodeBuild
                mv "$item" "${item}.tmp"
                ln -s "$(cat ${item}.tmp)" "$item"
                rm "${item}.tmp"
            else
                echo "Processing $item"
            fi            

        fi
    done
    
    ls -l
    cd -
}

create_symlinks "../../lambda-functions/iframe-generator-function/" "routes static syntrillo templates api.py flask_app.py"
create_symlinks "../../lambda-functions/message-endpoint-function/" "routes static syntrillo templates api.py"
create_symlinks "../../lambda-functions/blood-pressure-notification-function/" "syntrillo"
create_symlinks "../../lambda-functions/remote-monitoring-data-sync-function/" "syntrillo"
create_symlinks "../../lambda-functions/healthie-data-ingestor-function/" "syntrillo"
create_symlinks "../../lambda-functions/pii-data-sync-function/" "syntrillo"

create_symlinks "../../../../PythonAnywhere/website/static/healthie/documents/" "questionnaire_template_latest.xlsx"