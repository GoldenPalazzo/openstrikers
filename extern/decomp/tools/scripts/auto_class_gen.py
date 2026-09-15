#!/usr/bin/env python

import os
import re
import sys
import subprocess
from pathlib import Path

def extract_untranslated_obj_files(splits_file):
    """Extract all .o files from splits.txt that haven't been translated to .cpp files"""
    untranslated_files = []
    
    try:
        with open(splits_file, 'r') as f:
            lines = f.readlines()
            
        for line in lines:
            line = line.strip()
            if line.endswith('.o:'):
                # This is an untranslated object file
                obj_name = line[:-1]  # Remove the ':'
                untranslated_files.append(obj_name)
                
    except FileNotFoundError:
        print(f"Error: Could not find {splits_file}")
        return []
        
    return untranslated_files

def parse_dwarf_for_source_paths(dwarf_file):
    """Parse dwarf_ouput2.txt to build a mapping of object files to their original source paths"""
    obj_to_source_map = {}
    
    try:
        with open(dwarf_file, 'r') as f:
            lines = f.readlines()
            
        current_obj = None
        for line in lines:
            line = line.strip()
            
            # Look for compile unit lines that show the original source path
            if line.startswith('Compile unit:'):
                # Extract the path: "Compile unit: D:\project\mariosoccer\global\src\ai\AILoader.cpp"
                match = re.search(r'Compile unit: (.+)', line)
                if match:
                    source_path = match.group(1)
                    
                    # Convert Windows path to Unix and extract relative path
                    # D:\project\mariosoccer\global\src\ai\AILoader.cpp -> ai/AILoader.cpp
                    # or D:\project\mariosoccer\engine\global\src\core\nlAVLTree.h -> core/nlAVLTree.h
                    
                    # Handle different base paths
                    if '\\global\\src\\' in source_path:
                        # Extract path after global\src\
                        parts = source_path.split('\\global\\src\\')
                        if len(parts) > 1:
                            rel_path = parts[1].replace('\\', '/')
                            # Get the base filename without extension
                            base_name = os.path.splitext(os.path.basename(rel_path))[0]
                            obj_to_source_map[f"{base_name}.o"] = rel_path
                            
    except FileNotFoundError:
        print(f"Error: Could not find {dwarf_file}")
        return {}
        
    return obj_to_source_map

def determine_output_directories(source_path):
    """Determine the output directories for src and include based on the source path"""
    # Extract directory from source path
    dir_path = os.path.dirname(source_path)
    
    # Determine if it should go in src or include based on file extension
    filename = os.path.basename(source_path)
    is_header = filename.endswith('.h')
    
    if is_header:
        # Headers go to include directory
        src_dir = os.path.join('src/_class_gen', dir_path)
        include_dir = os.path.join('include/_class_gen', dir_path)
    else:
        # Source files
        src_dir = os.path.join('src/_class_gen', dir_path)
        include_dir = os.path.join('include/_class_gen', dir_path)
    
    return src_dir, include_dir

def run_class_gen_on_obj_file(obj_file, output_src_dir, output_include_dir, search_dir, class_gen_script, inline_deferred=False):
    """Run the existing class_gen.py script on a single object file"""
    
    # Create output directories
    os.makedirs(output_src_dir, exist_ok=True)
    os.makedirs(output_include_dir, exist_ok=True)
    
    # Create a temporary output directory for class_gen
    temp_output_dir = os.path.join('src/_class_gen', 'temp')
    os.makedirs(temp_output_dir, exist_ok=True)
    
    try:
        # Run class_gen.py
        cmd = [
            'python', class_gen_script,
            '--obj-file', obj_file,
            '--output-dir', temp_output_dir,
            '--search-dir', search_dir
        ]
        
        # Add --inline-deferred if requested
        if inline_deferred:
            cmd.append('--inline-deferred')
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            # Move generated files to correct directories
            base_name = os.path.splitext(os.path.basename(obj_file))[0]
            
            # Move .cpp file to src directory
            temp_cpp = os.path.join(temp_output_dir, f"{base_name}.cpp")
            final_cpp = os.path.join(output_src_dir, f"{base_name}.cpp")
            if os.path.exists(temp_cpp):
                os.makedirs(os.path.dirname(final_cpp), exist_ok=True)
                os.rename(temp_cpp, final_cpp)
                print(f"Generated: {final_cpp}")
            
            # Move .h file to include directory  
            temp_h = os.path.join(temp_output_dir, f"{base_name}.h")
            final_h = os.path.join(output_include_dir, f"{base_name}.h")
            if os.path.exists(temp_h):
                os.makedirs(os.path.dirname(final_h), exist_ok=True)
                os.rename(temp_h, final_h)
                print(f"Generated: {final_h}")
                
            return True
        else:
            print(f"Error running class_gen on {obj_file}: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"Exception running class_gen on {obj_file}: {e}")
        return False
    finally:
        # Clean up temp directory
        if os.path.exists(temp_output_dir):
            try:
                os.rmdir(temp_output_dir)
            except:
                pass

def main():
    # Configuration
    splits_file = 'config/G4QE01/splits.txt'
    dwarf_file = 'dwarf_ouput2.txt'
    search_dir = 'build/G4QE01/asm'
    class_gen_script = 'tools/scripts/class_gen.py'
    inline_deferred = True  # Set to True to enable inline-deferred mode
    
    print("Auto Class Generator")
    print("===================")
    
    # Step 1: Extract untranslated .o files from splits.txt
    print("Step 1: Extracting untranslated .o files from splits.txt...")
    untranslated_files = extract_untranslated_obj_files(splits_file)
    print(f"Found {len(untranslated_files)} untranslated object files")
    
    if not untranslated_files:
        print("No untranslated files found!")
        return
    
    # Step 2: Parse dwarf output to map object files to source paths
    print("\nStep 2: Parsing dwarf_ouput2.txt for source directory mapping...")
    obj_to_source_map = parse_dwarf_for_source_paths(dwarf_file)
    print(f"Found source path mappings for {len(obj_to_source_map)} files")
    
    # Step 3: Process each untranslated file
    print("\nStep 3: Processing untranslated files...")
    
    success_count = 0
    total_count = 0
    
    for obj_file in untranslated_files:
        total_count += 1
        print(f"\nProcessing {obj_file} ({total_count}/{len(untranslated_files)})...")
        
        # Get source path mapping
        if obj_file in obj_to_source_map:
            source_path = obj_to_source_map[obj_file]
            print(f"  Source path: {source_path}")
            
            # Determine output directories
            output_src_dir, output_include_dir = determine_output_directories(source_path)
            print(f"  Output src: {output_src_dir}")
            print(f"  Output include: {output_include_dir}")
            
            # Run class_gen
            if run_class_gen_on_obj_file(obj_file, output_src_dir, output_include_dir, search_dir, class_gen_script, inline_deferred):
                success_count += 1
                print(f"  ✓ Successfully processed {obj_file}")
            else:
                print(f"  ✗ Failed to process {obj_file}")
        else:
            print(f"  ✗ No source path mapping found for {obj_file}")
    
    print(f"\nSummary:")
    print(f"  Total files: {total_count}")
    print(f"  Successfully processed: {success_count}")
    print(f"  Failed: {total_count - success_count}")

if __name__ == "__main__":
    main()
