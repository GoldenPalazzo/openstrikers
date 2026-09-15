# Function Analysis Script Manual

## Overview

The `funcs_analysis.py` script is a powerful tool for analyzing decompiled functions in the Super Mario Strikers decompilation project. It provides detailed information about function sizes, match percentages, virtual addresses, and file locations, making it easier to identify and prioritize functions for further decompilation work.

## Credits

**This script is a modified version of the `easy_funcs.py` script from the [Super Smash Bros Melee decompilation project](https://github.com/doldecomp/melee).**

The original script was created by the talented developers of the Melee decompilation project, and this version has been adapted and enhanced for use with the Super Mario Strikers decompilation project.

## Dependencies

Before using this script, ensure you have the following Python packages installed:

```bash
pip install humanfriendly prettytable
```

## Usage

### Basic Usage

```bash
python3 funcs_analysis.py [OPTIONS] [UNITS...]
```

### Arguments

- `UNITS` (optional): Directories or files to search within the project. If not specified, searches all units.

### Options

#### Filtering Options

| Option | Description | Default |
|--------|-------------|---------|
| `-s, --min-size BYTES` | Minimum function size in bytes | 0 |
| `-S, --max-size BYTES` | Maximum function size in bytes | 512 |
| `-v, --min-virtual-address HEX` | Minimum virtual address (hex) | 0 |
| `-V, --max-virtual-address HEX` | Maximum virtual address (hex) | 0xFFFFFFFF |
| `-m, --min-matched PERCENT` | Minimum fuzzy match percentage | 0 |
| `-M, --max-matched PERCENT` | Maximum fuzzy match percentage | 0 |

#### Display Options

| Option | Description | Default |
|--------|-------------|---------|
| `-n, --max-results RESULTS` | Maximum number of functions to display | 0 (unlimited) |
| `-o, --names-only` | Print only function names | False |
| `--file-summary` | Show summary of functions per file | False |
| `--max-name-length LENGTH` | Maximum function name length before truncation | 50 |
| `--show-full-names` | Show full function names without truncation | False |

#### Sorting Options

| Option | Description |
|--------|-------------|
| `-a, --order-by-address` | Sort functions by virtual address |
| `-f, --order-by-file` | Sort functions by file name |
| (default) | Sort by size, then by address |

## Examples

### Find all small functions (under 100 bytes)

```bash
python3 funcs_analysis.py -S 100
```

### Find functions in a specific directory

```bash
python3 funcs_analysis.py Game/Render
```

### Find functions with high match percentage

```bash
python3 funcs_analysis.py -m 80
```

### Get a summary of functions per file

```bash
python3 funcs_analysis.py --file-summary
```

### Find functions in a specific address range

```bash
python3 funcs_analysis.py -v 0x80000000 -V 0x80010000
```

### Get only function names for easy functions

```bash
python3 funcs_analysis.py -S 200 -m 50 -o
```

### Sort by file and limit results

```bash
python3 funcs_analysis.py -f -n 20
```

## Output Format

### Standard Table Output

The script displays results in a formatted table with the following columns:

- **Address**: Virtual address of the function (hex)
- **File**: Source file path relative to project root
- **Function**: Function name (may be truncated for readability)
- **Size**: Function size in human-readable format
- **Matched**: Fuzzy match percentage

### File Summary Mode

When using `--file-summary`, the output shows:

- **File**: Source file path
- **Functions**: Number of matching functions in the file
- **Total Size**: Combined size of all matching functions

### Names Only Mode

When using `--names-only`, only function names are printed, one per line.

## How It Works

1. **Build Process**: The script automatically runs `ninja` to build the project and generate the report file (`build/G4QE01/report.json`)

2. **Data Parsing**: It parses the JSON report to extract function information including:
   - Function names
   - Unit (module) names
   - Function sizes
   - Fuzzy match percentages
   - Virtual addresses

3. **Filtering**: Functions are filtered based on the specified criteria (size, match percentage, address range)

4. **Sorting**: Results are sorted according to the specified ordering method

5. **Display**: Results are formatted and displayed in the requested format

## Tips for Decompilation Work

- **Start with small functions**: Use `-S 100` to find functions under 100 bytes
- **Focus on well-matched functions**: Use `-m 80` to find functions with high match percentages
- **Work by file**: Use `-f` to group functions by file for systematic decompilation
- **Use file summary**: Use `--file-summary` to identify files with many easy functions
- **Combine filters**: Use multiple filters together to narrow down your search

## Troubleshooting

### Common Issues

1. **Build errors**: Ensure the project builds successfully before running the script
2. **Missing dependencies**: Install required Python packages
3. **Permission errors**: Ensure you have read/write access to the project directory

### Error Messages

- If the build fails, the script will display the build output and exit
- If the report file is missing, ensure the project has been built at least once
- If no functions match the criteria, try relaxing the filter parameters

## Integration with Decompilation Workflow

This script is designed to integrate seamlessly with the decompilation workflow:

1. **Discovery**: Use it to find functions that are good candidates for decompilation
2. **Prioritization**: Sort by size or match percentage to prioritize your work
3. **Organization**: Use file-based sorting to work systematically through the codebase
4. **Progress Tracking**: Use the file summary to track progress across different files

## License

Project-original portions of this script and documentation are offered under
CC0 1.0 to the extent their contributors own the relevant rights. Third-party
material remains subject to its own terms. See the repository's root
[`LICENSE`](../../LICENSE) and
[`THIRD_PARTY_NOTICES.md`](../../THIRD_PARTY_NOTICES.md).
