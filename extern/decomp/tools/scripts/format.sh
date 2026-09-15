#!/bin/bash

# Check if a file path is provided
if [ $# -eq 0 ]; then
    echo "Usage: $0 <file_path>"
    exit 1
fi

# Get the file path from the first argument
FILE_PATH="$1"

# Check if the file exists
if [ ! -f "$FILE_PATH" ]; then
    echo "Error: File '$FILE_PATH' does not exist"
    exit 1
fi

# Run clang-format on the file
clang-format -i "$FILE_PATH"

echo "Formatted $FILE_PATH"
