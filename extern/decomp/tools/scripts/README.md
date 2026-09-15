# class_gen.py Documentation

## Overview
`class_gen.py` is a Python script designed to generate C++ header (.h) and implementation (.cpp) files from assembly (.s) files. It analyzes assembly files to extract function declarations and metadata, then generates corresponding C++ class structures and function stubs.

## Features
- Extracts function metadata (offset, address, size) from assembly files
- Identifies class methods and standalone functions
- Generates header files with proper include guards and class declarations
- Creates implementation files with function stubs
- Supports both single file and batch processing

## Usage

### Command Line Arguments
- `--class-file`: Path to a text file containing a list of object files to process
- `--obj-file`: Path to a single object file to process
- `--output-dir`: Output directory for generated files (default: 'src/_class_gen')
- `--search-dir`: Directory to search for .s files (default: 'build/G4QE01/asm')

### Examples

1. Process a single object file:
```bash
python class_gen.py --obj-file build/G4QE01/obj/Game/PhysicsObject.o --search-dir ./build/G4QE01/asm/Game
```
This will:
- Look for `PhysicsObject.s` in the specified search directory
- Generate `PhysicsObject.h` and `PhysicsObject.cpp` in the output directory
- Extract all functions and their metadata from the assembly file

2. Process multiple files from a class list:
```bash
python class_gen.py --class-file class.txt
```
Where `class.txt` contains:
```
nlAVLTree.o
nlDebug.o
nlDebugFile.o
```
This will:
- Process each object file listed in `class.txt`
- Generate corresponding .h and .cpp files for each
- Place all generated files in the output directory

## Output Format

### Header File (.h)
- Include guard
- Forward declarations for standalone functions
- Class declarations with their methods
- Proper C++ class structure

### Implementation File (.cpp)
- Include statement for the corresponding header
- Function stubs with metadata comments
- Empty function bodies ready for implementation

## Notes
- The script automatically creates the output directory if it doesn't exist
- Function metadata includes offset, address, and size information
- Class methods are identified by the presence of `::` in the function declaration
- The script maintains proper C++ syntax and formatting in generated files
