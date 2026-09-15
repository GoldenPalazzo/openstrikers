#!/usr/bin/env python3
"""
Generic script to convert assembly sound properties arrays to C++ static array declarations.
Extracts @string references and converts them to actual string values.
"""

import re
import struct
import sys
import os
import argparse

def hex_to_float(hex_str):
    """Convert hex string to float."""
    # Remove 0x prefix if present
    if hex_str.startswith('0x'):
        hex_str = hex_str[2:]
    
    # Convert hex to bytes and then to float
    hex_bytes = bytes.fromhex(hex_str)
    # Reverse bytes for little-endian (PowerPC is big-endian, but this is how it's stored)
    hex_bytes = hex_bytes[::-1]
    return struct.unpack('f', hex_bytes)[0]

def format_float(value):
    """Format float value to reasonable precision."""
    # Round to 2 decimal places for common values
    if abs(value - 0.5) < 0.001:
        return "0.5f"
    elif abs(value - 0.3) < 0.001:
        return "0.3f"
    elif abs(value - 0.4) < 0.001:
        return "0.4f"
    elif abs(value - 0.6) < 0.001:
        return "0.6f"
    elif abs(value - 0.7) < 0.001:
        return "0.7f"
    elif abs(value - 0.8) < 0.001:
        return "0.8f"
    elif abs(value - 0.9) < 0.001:
        return "0.9f"
    elif abs(value - 1.0) < 0.001:
        return "1.0f"
    elif abs(value - 0.0) < 0.001:
        return "0.0f"
    else:
        # For other values, round to 2 decimal places
        return f"{round(value, 2)}f"

def extract_string_references(assembly_text):
    """Extract all @string references from the assembly file."""
    string_refs = set()
    pattern = r'@(\w+)'
    
    for match in re.finditer(pattern, assembly_text):
        string_refs.add(match.group(0))
    
    return sorted(list(string_refs))

def find_sound_properties_section(assembly_text, verbose=False):
    """Find the SoundProperties section in the assembly file."""
    # Look for patterns like:
    # .obj WORLDSoundProperties, global
    # .obj YOSHISoundProperties, global
    # etc.
    
    # First, find the .obj line
    obj_pattern = r'\.obj\s+(\w+SoundProperties),\s+global'
    obj_match = re.search(obj_pattern, assembly_text)
    
    if not obj_match:
        if verbose:
            print("Could not find .obj line for SoundProperties")
        return None, None
    
    section_name = obj_match.group(1)
    if verbose:
        print(f"Found .obj line: {section_name}")
    
    # Find the start and end of the section
    start_pattern = rf'\.obj\s+{re.escape(section_name)},\s+global'
    end_pattern = rf'\.endobj\s+{re.escape(section_name)}'
    
    start_match = re.search(start_pattern, assembly_text)
    end_match = re.search(end_pattern, assembly_text)
    
    if not start_match:
        if verbose:
            print("Could not find start of section")
        return None, None
    
    start_pos = start_match.end()
    end_pos = end_match.start() if end_match else len(assembly_text)
    
    section_content = assembly_text[start_pos:end_pos]
    
    if verbose:
        print(f"Section content length: {len(section_content)}")
        print(f"First 200 chars: {section_content[:200]}")
    
    return section_name, section_content

def parse_sound_properties_section(section_content, verbose=False):
    """Parse the SoundProperties section and extract the data."""
    entries = []
    
    # Split into lines and process each line
    lines = section_content.strip().split('\n')
    
    current_entry = []
    line_count = 0
    
    if verbose:
        print(f"Processing {len(lines)} lines in section")
    
    for line in lines:
        line = line.strip()
        line_count += 1
        
        # Skip empty lines and comments, but NOT .4byte lines
        if not line or line.startswith('#'):
            continue
        
        # Skip non-.4byte directives
        if line.startswith('.') and not line.startswith('.4byte'):
            continue
            
        # Look for .4byte directives
        if line.startswith('.4byte'):
            # Extract the value after .4byte
            match = re.search(r'\.4byte\s+(.+)$', line)
            if match:
                value = match.group(1).strip()
                current_entry.append(value)
                
                # Each entry has 7 fields
                if len(current_entry) == 7:
                    entries.append(current_entry)
                    current_entry = []
                    
                    if verbose and len(entries) <= 3:  # Debug first few entries
                        print(f"Entry {len(entries)}: {entries[-1]}")
    
    if verbose:
        print(f"Found {len(entries)} complete entries")
        if entries:
            print(f"First entry: {entries[0]}")
    
    return entries

def generate_string_mapping(string_refs, assembly_text, verbose=False):
    """Generate a mapping from @string references to actual string values."""
    string_map = {}
    
    # Extract string values directly from the assembly file
    for ref in string_refs:
        # Look for the string definition in the assembly file
        # Pattern: .obj "@149", local
        #          .string "WORLDSFX_FE_TOGGLE"
        pattern = rf'\.obj\s+"{re.escape(ref)}",\s+local\s*\n\s*\.string\s+"([^"]+)"'
        match = re.search(pattern, assembly_text)
        
        if match:
            string_value = match.group(1)
            string_map[ref] = string_value
        else:
            # Fallback: create placeholder
            num = ref[1:]  # Remove @
            string_map[ref] = f"STRING_{num}"
    
    if verbose:
        print(f"Generated string mapping for {len([k for k, v in string_map.items() if not v.startswith('STRING_')])} actual strings")
        print(f"Using placeholders for {len([k for k, v in string_map.items() if v.startswith('STRING_')])} missing strings")
    
    return string_map

def generate_cpp_array(section_name, entries, string_map):
    """Generate the C++ array declaration."""
    cpp_lines = []
    cpp_lines.append(f'static SoundProperties {section_name}[] = {{')
    
    for i, entry in enumerate(entries):
        event_name_ref, sound_name_ref, f0_hex, f1_hex, f2_hex, i0_hex, i1_hex = entry
        
        # Convert string references to actual strings
        # Remove quotes from the references first
        event_name_clean = event_name_ref.strip('"')
        sound_name_clean = sound_name_ref.strip('"')
        event_name = string_map.get(event_name_clean, event_name_clean)
        sound_name = string_map.get(sound_name_clean, sound_name_clean)
        
        # Convert hex values to appropriate types
        f0 = hex_to_float(f0_hex)
        f1 = hex_to_float(f1_hex)
        f2 = hex_to_float(f2_hex)
        i0 = int(i0_hex, 16) if i0_hex.startswith('0x') else int(i0_hex)
        i1 = int(i1_hex, 16) if i1_hex.startswith('0x') else int(i1_hex)
        
        # Format the line - one SoundProperties struct per line
        line = f'    {{ "{event_name}", "{sound_name}", {format_float(f0)}, {format_float(f1)}, {format_float(f2)}, {i0}, {i1} }}'
        
        # Add comma if not the last entry
        if i < len(entries) - 1:
            line += ','
        
        cpp_lines.append(line)
    
    cpp_lines.append('};')
    
    return '\n'.join(cpp_lines)

def main():
    parser = argparse.ArgumentParser(description='Convert assembly sound properties arrays to C++ static array declarations')
    parser.add_argument('assembly_file', help='The assembly file to parse')
    parser.add_argument('cpp_file', nargs='?', help='Optional C++ file to extract string mappings from')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose output')
    
    args = parser.parse_args()
    
    assembly_file = args.assembly_file
    cpp_file = args.cpp_file
    verbose = args.verbose
    
    if not os.path.exists(assembly_file):
        print(f"Error: Assembly file '{assembly_file}' not found")
        sys.exit(1)
    
    if verbose:
        print(f"Parsing assembly file: {assembly_file}")
    
    # Read the assembly file
    try:
        with open(assembly_file, 'r') as f:
            assembly_text = f.read()
    except Exception as e:
        print(f"Error reading assembly file: {e}")
        sys.exit(1)
    
    # Extract string references
    string_refs = extract_string_references(assembly_text)
    if verbose:
        print(f"Found {len(string_refs)} string references: {string_refs[:10]}{'...' if len(string_refs) > 10 else ''}")
    
    # Find the SoundProperties section
    section_name, section_content = find_sound_properties_section(assembly_text, verbose)
    
    if not section_name:
        print("Error: Could not find SoundProperties section in assembly file")
        sys.exit(1)
    
    if verbose:
        print(f"Found SoundProperties section: {section_name}")
    
    # Parse the section
    entries = parse_sound_properties_section(section_content, verbose)
    
    if verbose:
        print(f"Found {len(entries)} entries")
    
    if len(entries) == 0:
        print("Error: No entries found. Check the assembly file format.")
        print("Expected format: .4byte directives with 7 values per entry")
        sys.exit(1)
    
    # Generate string mapping from the assembly text
    string_map = generate_string_mapping(string_refs, assembly_text, verbose)
    
    if verbose:
        print(f"Generated string mapping for {len(string_map)} references")
    
    # Generate C++ array
    cpp_array = generate_cpp_array(section_name, entries, string_map)
    
    # Generate output filename
    output_file = f"{section_name.lower()}_generated.cpp"
    
    if verbose:
        print(f"\nGenerated C++ array:")
        print("=" * 80)
        print(cpp_array)
        print("=" * 80)
    
    # Save to file
    with open(output_file, 'w') as f:
        f.write(cpp_array)
    
    # Default output: just a success message
    print(f"✓ {assembly_file} → {output_file} ({len(entries)} entries)")
    
    if verbose:
        print(f"\nNote: You may need to manually update the string values in the generated array.")
        print(f"      The current mapping uses placeholder values like 'STRING_149'.")

if __name__ == "__main__":
    main()
