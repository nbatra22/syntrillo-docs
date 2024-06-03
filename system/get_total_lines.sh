#!/bin/bash

# Path: ignore_get_total_lines.sh
# description: This script will get the total lines of code in a project
# usage: ./ignore_get_total_lines.sh

# make sure we are in the directory of this script
cd "$(dirname "$(realpath "${BASH_SOURCE[0]}")")";

# go one level up
cd ..

find . -type f \( -name "*.py" -o -name "*.html" \) -print0 | xargs -0 wc -l




