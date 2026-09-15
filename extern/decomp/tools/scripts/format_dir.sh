#!/bin/bash

# Check if directory parameter is provided
if [ $# -eq 0 ]; then
    echo "Usage: $0 <directory>"
    exit 1
fi

DIR="$1"

# Check if directory exists
if [ ! -d "$DIR" ]; then
    echo "Error: Directory '$DIR' does not exist"
    exit 1
fi

# Run clang-format on all .c files in the directory
clang-format -i "$DIR"/*.c 
clang-format -i "$DIR"/*.cpp 
