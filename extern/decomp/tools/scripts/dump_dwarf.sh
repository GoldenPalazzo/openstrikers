#!/bin/bash
#
# dump_dwarf.sh
#
# Dumps DWARF 1.1 debug information from the original Super Mario Strikers
# debug ELF (`MarioSoccerR.elf`) into a human-readable text file. The output
# file is consumed by tooling like `tools/scripts/auto_class_gen.py` to map
# object files back to their original source paths.
#
# If you have legally acquired the game yourself and have the debug ELF
# placed at `orig/G4QE01/MarioSoccerR.elf`, just run:
#
#     ./tools/scripts/dump_dwarf.sh
#
# The dump will be written to `dwarf.txt` in the project root.
#
# Optional arguments:
#     $1  Path to the input ELF (default: orig/G4QE01/MarioSoccerR.elf)
#     $2  Path to the output file (default: dwarf.txt)
#

set -e

# Resolve project root (this script lives in tools/scripts/).
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$PROJECT_ROOT"

INPUT_ELF="${1:-orig/G4QE01/MarioSoccerR.elf}"
OUTPUT_FILE="${2:-dwarf.txt}"
DTK="build/tools/dtk"

if [ ! -x "$DTK" ]; then
    echo "Error: dtk not found at '$DTK'."
    echo "Run 'python configure.py && ninja' once to download it."
    exit 1
fi

if [ ! -f "$INPUT_ELF" ]; then
    echo "Error: Input ELF '$INPUT_ELF' does not exist."
    echo "Place the original debug ELF at orig/G4QE01/MarioSoccerR.elf"
    echo "(only available if you legally acquired the game yourself)."
    exit 1
fi

echo "Dumping DWARF info from '$INPUT_ELF' -> '$OUTPUT_FILE'..."
"$DTK" dwarf dump --no-color --include-erased -o "$OUTPUT_FILE" "$INPUT_ELF"

echo "Done. Wrote $(wc -l < "$OUTPUT_FILE") lines to $OUTPUT_FILE."
