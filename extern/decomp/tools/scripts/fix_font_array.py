#!/usr/bin/env python3

def fix_font_array():
    with open('src/NL/gl/glFont.cpp', 'r') as f:
        content = f.read()
    
    # Find the array section
    start_marker = "const unsigned short _fontData[] = {"
    end_marker = "};"
    
    start_pos = content.find(start_marker)
    if start_pos == -1:
        print("Could not find array start marker")
        return
    
    # Find the end of the array
    array_start = start_pos + len(start_marker)
    array_end = content.find(end_marker, array_start)
    if array_end == -1:
        print("Could not find array end marker")
        return
    
    # Extract the array content
    array_content = content[array_start:array_end].strip()
    
    # Split into lines and add commas
    lines = array_content.split('\n')
    fixed_lines = []
    
    for line in lines:
        line = line.strip()
        if line.startswith('0x'):  # It's a hex value
            fixed_lines.append(line + ',')
        else:
            fixed_lines.append(line)  # Keep empty lines or other content as is
    
    # Join the fixed lines
    fixed_array_content = '\n'.join(fixed_lines)
    
    # Reconstruct the file content
    new_content = (
        content[:array_start] + 
        '\n' + fixed_array_content + '\n' +
        content[array_end:]
    )
    
    # Write back to file
    with open('src/NL/gl/glFont.cpp', 'w') as f:
        f.write(new_content)
    
    print("Fixed font array by adding commas between hex values")

if __name__ == "__main__":
    fix_font_array() 
