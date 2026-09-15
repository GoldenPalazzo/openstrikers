#!/usr/bin/env python3
"""
Generic script to convert animation properties assembly data to C++ arrays.
"""

import re
import sys
import os


def parse_assembly_file(file_path):
    """Parse the assembly file and extract the animation properties data."""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find the animation properties section - look for the array name
    # We'll search for the pattern .obj ARRAY_NAME, global
    array_name = None
    array_pattern = r'\.obj ([A-Za-z_]+), global'
    array_match = re.search(array_pattern, content)
    if array_match:
        array_name = array_match.group(1)
    
    if not array_name:
        raise ValueError("Could not find animation properties array name")
    
    start_marker = f".obj {array_name}, global"
    end_marker = f".endobj {array_name}"
    
    start_idx = content.find(start_marker)
    if start_idx == -1:
        raise ValueError(f"Could not find {array_name} start marker")
    
    end_idx = content.find(end_marker)
    if end_idx == -1:
        raise ValueError(f"Could not find {array_name} end marker")
    
    # Extract the data section
    data_section = content[start_idx:end_idx + len(end_marker)]
    
    # Extract string constants first
    string_constants = {}
    string_pattern = r'\.obj "@(\d+)", local\s*\n\t\.string "([^"]+)"'
    
    for match in re.finditer(string_pattern, content):
        const_id = match.group(1)
        string_value = match.group(2)
        string_constants[const_id] = string_value
    
    # Parse the data array
    data_pattern = r'\.4byte "@(\d+)"\s*\n\t\.4byte "@(\d+)"\s*\n\t\.4byte (0x[0-9A-Fa-f]+)\s*\n\t\.4byte (0x[0-9A-Fa-f]+)\s*\n\t\.4byte (0x[0-9A-Fa-f]+)\s*\n\t\.4byte (0x[0-9A-Fa-f]+)\s*\n\t\.4byte (0x[0-9A-Fa-f]+)\s*\n\t\.4byte (0x[0-9A-Fa-f]+)'
    
    entries = []
    for match in re.finditer(data_pattern, data_section):
        anim_name_id = match.group(1)
        anim_file_id = match.group(2)
        val1 = int(match.group(3), 16)
        val2 = int(match.group(4), 16)
        val3 = int(match.group(5), 16)
        val4 = int(match.group(6), 16)
        val5 = int(match.group(7), 16)
        val6 = int(match.group(8), 16)
        
        # Convert hex float to actual float
        import struct
        val2_float = struct.unpack('f', struct.pack('I', val2))[0]
        
        # Get the original strings
        anim_name = string_constants.get(anim_name_id, f"UNKNOWN_{anim_name_id}")
        anim_file = string_constants.get(anim_file_id, f"UNKNOWN_{anim_file_id}")
        
        # Keep the original strings as they are in the assembly file
        # No conversion needed - preserve GANIM_ prefixes
        
        entries.append({
            'anim_name': anim_name,
            'anim_file': anim_file,
            'val1': val1,
            'val2': val2_float,
            'val3': val3,
            'val4': val4,
            'val5': val5,
            'val6': val6
        })
    
    return entries, array_name


def generate_cpp_code(entries, array_name):
    """Generate C++ code for the animation properties array."""
    
    # Convert array name to camelCase for the count variable
    count_var_name = array_name[0].lower() + array_name[1:] + "Count"
    
    cpp_code = f"""#include "AnimProperties.h"

static AnimProperties {array_name}[] = {{
"""
    
    for i, entry in enumerate(entries):
        # Format the float value nicely
        val2_str = f"{entry['val2']:.6f}f"
        if val2_str.endswith('.000000f'):
            val2_str = f"{int(entry['val2'])}.0f"
        
        # Build the line without f-strings to avoid curly brace issues
        entry_line = "    { \"" + entry['anim_name'] + "\", \"" + entry['anim_file'] + "\", " + str(entry['val1']) + ", " + val2_str + ", " + str(entry['val3']) + ", " + str(entry['val4']) + ", " + str(entry['val5']) + ", " + str(entry['val6']) + " }"
        
        cpp_code += entry_line
        
        if i < len(entries) - 1:
            cpp_code += ","
        cpp_code += "\n"
    
    cpp_code += f"""}};

// Array size
static const int {count_var_name} = sizeof({array_name}) / sizeof({array_name}[0]);
"""
    
    return cpp_code


def main():
    if len(sys.argv) != 3:
        print("Usage: python convert_anim_properties.py <assembly_file> <array_name>")
        print("Example: python convert_anim_properties.py build/G4QE01/asm/goalieanimproperties.s GLOBALAnimProperties")
        print("Example: python convert_anim_properties.py build/G4QE01/asm/playeranimproperties.s PLAYERAnimProperties")
        sys.exit(1)
    
    assembly_file = sys.argv[1]
    array_name = sys.argv[2]
    
    try:
        print(f"Parsing assembly file: {assembly_file}")
        print(f"Target array name: {array_name}")
        
        entries, detected_array_name = parse_assembly_file(assembly_file)
        
        print(f"Detected array in assembly: {detected_array_name}")
        print(f"Found {len(entries)} animation property entries")
        
        # Generate C++ code
        cpp_code = generate_cpp_code(entries, array_name)
        
        # Generate output filename based on input
        input_basename = os.path.splitext(os.path.basename(assembly_file))[0]
        output_file = f"{input_basename}_converted.cpp"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(cpp_code)
        
        print(f"Generated C++ code in: {output_file}")
        print(f"Total entries: {len(entries)}")
        
        # Show first few entries as preview
        print("\nFirst 3 entries preview:")
        for i in range(min(3, len(entries))):
            entry = entries[i]
            print(f"  {i}: {entry['anim_name']} -> {entry['anim_file']}")
        
        print(f"\nOutput file: {output_file}")
        print("You can now manually copy the content to your project file.")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
