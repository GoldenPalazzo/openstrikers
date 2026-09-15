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

# Find and format all .c, .cpp, and .h files recursively
find "$DIR" -type f \( -name "*.c" -o -name "*.cpp" -o -name "*.h" \) -exec clang-format -i {} \;

echo "Formatting complete!" 
