#!/bin/bash

# Function to add the file path comment to Python files
add_file_path_comment() {
    local file=$1
    local update_path=$2
    # Determine the comment based on file extension
    if [[ $file == *.py ]]; then
        local comment="# Path: ${file}"
    elif [[ $file == *.html ]]; then
        local comment="<!-- Path: ${file} -->"
    else
        echo "Unsupported file type: $file"
        return
    fi

    # Check if the file is an __init__.py file
    if [[ "$(basename "$file")" == "__init__.py" ]]; then
        echo "Skipping __init__.py file: $file"
        return
    fi

    # Check if the first line of the file starts with "# ./Syntrillo_Clinic/" or "# Path:"
    local first_line=$(head -n 1 "$file")
    if [[ $first_line == "# ./Syntrillo_Clinic/"* ]]; then
        # Remove the first line if it starts with "# ./Syntrillo_Clinic/"
        sed -i '1d' "$file"
    fi

    if ${update_path} ; then
        if [[ $first_line == "# Path: "* ]]; then
            # Remove the first line if it starts with "# Path: "
            sed -i '1d' "$file"
        fi
    fi

    # Check if the first line of the file is already the comment
    first_line=$(head -n 1 "$file")
    if [ "$first_line" != "$comment" ]; then
        # Escape slashes in the comment to avoid issues with sed
        escaped_comment=$(echo "$comment" | sed 's/\//\\\//g')

        # Add the comment at the top of the file
        sed -i "1s/^/${escaped_comment}\n/" "$file"

        echo "Added comment to $file"
    else
        echo "Comment already present in $file"
    fi
}


# -----------
# Loop through all the directories one level above this script and find Python and HTML files

# make sure we are in the directory of this script
cd "$(dirname "$(realpath "${BASH_SOURCE[0]}")")";

# go one level up
cd ..

find ./ -type f \( -name "*.py" -o -name "*.html" \) | while read -r file; do
    add_file_path_comment "$file" true
done
