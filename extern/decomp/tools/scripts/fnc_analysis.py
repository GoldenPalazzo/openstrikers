#!/usr/bin/env python3
"""
Script to extract and filter function data from decompilation report JSON.
Extracts unit names, function sizes, fuzzy match percentages, and demangled names.
Supports export to both text and CSV formats with min/max size and percentage filters.
"""

import json
import sys
import csv
from typing import List, Dict, Any, Tuple

def load_report(file_path: str) -> Dict[str, Any]:
    """Load the JSON report from file."""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in file '{file_path}': {e}")
        sys.exit(1)

def extract_function_data(units: List[Dict[str, Any]]) -> List[Tuple[str, str, int, float, str]]:
    """
    Extract function data from units.
    Returns list of tuples: (unit_name, function_name, size, fuzzy_match_percent, demangled_name)
    """
    function_data = []
    
    for unit in units:
        unit_name = unit.get('name', 'Unknown')
        functions = unit.get('functions', [])
        
        for func in functions:
            func_name = func.get('name', 'Unknown')
            size = int(func.get('size', '0'))
            fuzzy_match_percent = float(func.get('fuzzy_match_percent', 0.0))
            demangled_name = func.get('metadata', {}).get('demangled_name', func_name)
            
            function_data.append((unit_name, func_name, size, fuzzy_match_percent, demangled_name))
    
    return function_data

def filter_and_sort_functions(function_data: List[Tuple[str, str, int, float, str]], 
                            min_size: int = None,
                            max_size: int = None, 
                            min_percent: float = None,
                            max_percent: float = None) -> List[Tuple[str, str, int, float, str]]:
    """
    Filter functions by size and fuzzy match percentage, then sort by size (ascending).
    
    Args:
        function_data: List of function tuples
        min_size: Minimum function size to include (None for no limit)
        max_size: Maximum function size to include (None for no limit)
        min_percent: Minimum fuzzy match percentage to include (None for no limit)
        max_percent: Maximum fuzzy match percentage to include (None for no limit)
    
    Returns:
        Filtered and sorted list of function tuples
    """
    filtered = function_data
    
    if min_size is not None:
        filtered = [f for f in filtered if f[2] >= min_size]
    
    if max_size is not None:
        filtered = [f for f in filtered if f[2] <= max_size]
    
    if min_percent is not None:
        filtered = [f for f in filtered if f[3] >= min_percent]
    
    if max_percent is not None:
        filtered = [f for f in filtered if f[3] <= max_percent]
    
    # Sort by size (ascending), then by fuzzy match percentage (ascending)
    return sorted(filtered, key=lambda x: (x[2], x[3]))

def print_function_list(function_data: List[Tuple[str, str, int, float, str]], 
                       show_demangled: bool = True):
    """Print the function list in a formatted way."""
    print(f"{'Unit Name':<50} {'Size':<8} {'Match %':<8} {'Demangled Name'}")
    print("-" * 100)
    
    for unit_name, func_name, size, fuzzy_percent, demangled_name in function_data:
        display_name = demangled_name if show_demangled else func_name
        print(f"{unit_name:<50} {size:<8} {fuzzy_percent:<8.2f} {display_name}")

def save_to_text_file(function_data: List[Tuple[str, str, int, float, str]], 
                     total_functions: int, min_size: int, max_size: int, 
                     min_percent: float, max_percent: float, output_file: str):
    """Save function data to a text file."""
    with open(output_file, 'w') as f:
        f.write("Function Decompilation Tasks\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"Total functions: {total_functions}\n")
        f.write(f"Filtered functions: {len(function_data)}\n")
        f.write(f"Size range: {min_size if min_size else 'None'} - {max_size if max_size else 'None'}\n")
        f.write(f"Match % range: {min_percent if min_percent else 'None'} - {max_percent if max_percent else 'None'}\n\n")
        
        f.write(f"{'Unit Name':<50} {'Size':<8} {'Match %':<8} {'Demangled Name'}\n")
        f.write("-" * 100 + "\n")
        
        for unit_name, func_name, size, fuzzy_percent, demangled_name in function_data:
            f.write(f"{unit_name:<50} {size:<8} {fuzzy_percent:<8.2f} {demangled_name}\n")

def save_to_csv_file(function_data: List[Tuple[str, str, int, float, str]], 
                    total_functions: int, min_size: int, max_size: int,
                    min_percent: float, max_percent: float, output_file: str):
    """Save function data to a CSV file."""
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        # Write header
        writer.writerow(['Unit Name', 'Size', 'Fuzzy Match %', 'Demangled Name'])
        
        # Write data
        for unit_name, func_name, size, fuzzy_percent, demangled_name in function_data:
            writer.writerow([unit_name, size, f"{fuzzy_percent:.2f}", demangled_name])

def main():
    if len(sys.argv) < 2:
        print("Usage: python extract_functions.py <report.json> [min_size] [max_size] [min_percent] [max_percent] [--csv]")
        print("Example: python extract_functions.py report.json 50 200 20.0 80.0 --csv")
        print("Options:")
        print("  --csv    Export to CSV format instead of text")
        print("Filters:")
        print("  min_size     Minimum function size in bytes (None for no limit)")
        print("  max_size     Maximum function size in bytes (None for no limit)")
        print("  min_percent  Minimum fuzzy match percentage (None for no limit)")
        print("  max_percent  Maximum fuzzy match percentage (None for no limit)")
        sys.exit(1)
    
    file_path = sys.argv[1]
    min_size = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2] != 'None' else None
    max_size = int(sys.argv[3]) if len(sys.argv) > 3 and sys.argv[3] != 'None' else None
    min_percent = float(sys.argv[4]) if len(sys.argv) > 4 and sys.argv[4] != 'None' else None
    max_percent = float(sys.argv[5]) if len(sys.argv) > 5 and sys.argv[5] != 'None' else None
    export_csv = '--csv' in sys.argv
    
    print(f"Loading report from: {file_path}")
    report = load_report(file_path)
    
    print("Extracting function data...")
    function_data = extract_function_data(report.get('units', []))
    
    print(f"Found {len(function_data)} functions total")
    
    if any([min_size, max_size, min_percent, max_percent]):
        filter_desc = []
        if min_size is not None:
            filter_desc.append(f"min_size={min_size}")
        if max_size is not None:
            filter_desc.append(f"max_size={max_size}")
        if min_percent is not None:
            filter_desc.append(f"min_percent={min_percent}")
        if max_percent is not None:
            filter_desc.append(f"max_percent={max_percent}")
        
        print(f"Filtering functions ({', '.join(filter_desc)})...")
        filtered_data = filter_and_sort_functions(function_data, min_size, max_size, min_percent, max_percent)
        print(f"Found {len(filtered_data)} functions after filtering")
    else:
        filtered_data = sorted(function_data, key=lambda x: (x[2], x[3]))
    
    print("\nFunction List (sorted by size, then by match percentage):")
    print_function_list(filtered_data)
    
    # Save to file
    file_extension = "csv" if export_csv else "txt"
    output_file = f"function_decompilation_tasks.{file_extension}"
    
    if export_csv:
        print(f"\nSaving to CSV: {output_file}")
        save_to_csv_file(filtered_data, len(function_data), min_size, max_size, min_percent, max_percent, output_file)
    else:
        print(f"\nSaving to text file: {output_file}")
        save_to_text_file(filtered_data, len(function_data), min_size, max_size, min_percent, max_percent, output_file)
    
    print(f"Results saved to: {output_file}")

if __name__ == "__main__":
    main()
