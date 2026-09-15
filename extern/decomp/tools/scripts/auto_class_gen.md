# auto_class_gen.py Documentation

## Overview
`auto_class_gen.py` is a script that automates the process of generating C++ header and implementation files from untranslated object files in the Super Mario Strikers decompilation project.

## Features
- Automatically extracts all untranslated `.o` files from `splits.txt`
- Maps object files to their original source directory structure using `dwarf_ouput2.txt`
- Runs the existing `class_gen.py` script on each object file
- Places generated files in the correct directory hierarchy within `./src/_class_gen`
- Provides detailed progress reporting and error handling

## How It Works

### Step 1: Extract Untranslated Files
The script analyzes `config/G4QE01/splits.txt` to identify all entries ending with `.o:` - these represent object files that haven't been translated to C++ source files yet.

### Step 2: Parse Directory Structure
The script parses `dwarf_ouput2.txt` to find "Compile unit:" entries that show the original Windows source paths (e.g., `D:\project\mariosoccer\global\src\ai\AILoader.cpp`). It converts these to Unix-style relative paths and maps each object file to its source directory.

### Step 3: Generate Files
For each untranslated object file:
1. Determines the correct output directories based on the original source path
2. Runs `class_gen.py` to generate header and implementation files
3. Places the generated files in the appropriate directory structure within `src/_class_gen`

## Usage

### Basic Usage
```bash
cd /path/to/smstrikers-decomp
python tools/scripts/auto_class_gen.py
```

### Requirements
- The script expects to be run from the project root directory
- Requires the following files to exist:
  - `config/G4QE01/splits.txt`
  - `dwarf_ouput2.txt`
  - `tools/scripts/class_gen.py`
  - `build/G4QE01/asm/` (directory with assembly files)

### Output Structure
Generated files are placed in `src/_class_gen/` with the same directory structure as the original source files:

```
src/_class_gen/
├── ai/
│   ├── AILoader.cpp
│   ├── AILoader.h
│   ├── AiUtil.cpp
│   └── AiUtil.h
├── core/
│   ├── nlAVLTree.cpp
│   └── nlAVLTree.h
└── ...
```

## Configuration
The script uses hardcoded paths that can be modified at the top of the `main()` function:

```python
splits_file = 'config/G4QE01/splits.txt'
dwarf_file = 'dwarf_ouput2.txt'
search_dir = 'build/G4QE01/asm'
class_gen_script = 'tools/scripts/class_gen.py'
```

## Error Handling
- Reports files that cannot be found in the assembly directory
- Reports object files that don't have source path mappings
- Provides a summary of successful vs failed processing
- Handles missing files gracefully with informative error messages

## Example Output
```
Auto Class Generator
===================
Step 1: Extracting untranslated .o files from splits.txt...
Found 19 untranslated object files

Step 2: Parsing dwarf_ouput2.txt for source directory mapping...
Found source path mappings for 15 files

Step 3: Processing untranslated files...

Processing AILoader.o (1/19)...
  Source path: ai/AILoader.cpp
  Output src: src/_class_gen/ai
  Output include: include/_class_gen/ai
  Generated: src/_class_gen/ai/AILoader.cpp
  Generated: include/_class_gen/ai/AILoader.h
  ✓ Successfully processed AILoader.o

...

Summary:
  Total files: 19
  Successfully processed: 15
  Failed: 4
```

## Notes
- The script creates temporary directories as needed
- Generated files use the same naming convention as the original `class_gen.py`
- Files are organized to match the original source directory structure
- The script is designed to be run multiple times safely
