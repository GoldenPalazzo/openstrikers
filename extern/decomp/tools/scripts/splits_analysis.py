#!/usr/bin/env python

def read_splits(splits_path):
    """
    Read and parse a splits file, extracting only .text sections.
    
    Args:
        splits_path (str): Path to the splits file
        
    Returns:
        dict: Dictionary mapping object names to their .text sections
              Each section is a tuple of (start, end)
    """
    splits = {}
    current_object = None
    
    try:
        with open(splits_path, 'r') as f:
            for line in f:
                line = line.strip()
                
                # Skip empty lines
                if not line:
                    continue
                    
                # Check if this is an object name line
                if line.endswith(':'):
                    current_object = line[:-1]  # Remove the colon
                    splits[current_object] = []
                    continue
                
                # If we have a current object, check if this is a .text line
                if current_object:
                    parts = line.split()
                    # Check if this is a .text line by looking at the first part
                    if parts and parts[0] == '.text':
                        # Find start and end addresses in the parts
                        start = None
                        end = None
                        for part in parts:
                            if part.startswith('start:'):
                                start = int(part.replace('start:', ''), 16)
                            elif part.startswith('end:'):
                                end = int(part.replace('end:', ''), 16)
                        
                        if start is not None and end is not None:
                            splits[current_object].append((start, end))
    
    except FileNotFoundError:
        print(f"Error: Could not find splits file at {splits_path}")
        return {}
    except Exception as e:
        print(f"Error reading splits file: {e}")
        return {}
        
    return splits

def read_symbols(symbols_path, symbol_filter=None):
    """
    Read and parse a symbols file.
    
    Args:
        symbols_path (str): Path to the symbols file
        symbol_filter (str, optional): Filter symbols by name prefix
        
    Returns:
        dict: Dictionary mapping addresses to symbol names
    """
    symbols = {}
    
    try:
        with open(symbols_path, 'r') as f:
            for line in f:
                line = line.strip()
                
                # Skip empty lines
                if not line:
                    continue
                
                # Parse symbol line (format: symbol_name = .text:0xADDRESS; // type:...)
                if '=' in line and '.text:' in line:
                    try:
                        # Split at '=' and get symbol name and address part
                        symbol_part, address_part = line.split('=', 1)
                        symbol_name = symbol_part.strip()
                        
                        # Apply filter if specified
                        if symbol_filter and not symbol_name.startswith(symbol_filter):
                            continue
                        
                        # Extract address from .text:0xADDRESS
                        address_str = address_part.split(';')[0].strip()
                        if '.text:' in address_str:
                            address = int(address_str.split('.text:')[1], 16)
                            symbols[address] = symbol_name
                    except (ValueError, IndexError):
                        continue  # Skip lines that don't match the expected format
    
    except FileNotFoundError:
        print(f"Error: Could not find symbols file at {symbols_path}")
        return {}
    except Exception as e:
        print(f"Error reading symbols file: {e}")
        return {}
        
    return symbols


# Example usage:
if __name__ == "__main__":
    # Define root directory (where splits.txt and symbols.txt are located)
    root_dir = "config/G4QE01"
    
    # Read both files
    splits = read_splits(f"{root_dir}/splits.txt")
    # symbols = read_symbols(f"{root_dir}/symbols.txt", symbol_filter="nl")
    symbols = read_symbols(f"{root_dir}/symbols.txt")
    
    # Write results to a text file
    output_file = "splits_analysis.txt"
    try:
        with open(output_file, 'w') as f:
            # First, find which sections contain our filtered symbols
            sections_with_symbols = set()
            for addr, symbol in symbols.items():
                for obj_name, sections in splits.items():
                    for start, end in sections:
                        if start <= addr <= end:
                            sections_with_symbols.add((obj_name, start, end))
            
            # Write only sections that contain our filtered symbols
            for obj_name, start, end in sorted(sections_with_symbols):
                f.write(f"\nObject: {obj_name}\n")
                f.write(f"  Start: 0x{start:08X}, End: 0x{end:08X}\n")
                f.write(f"  Size: {end - start} bytes\n")
                
                # Write symbols that fall within this range
                f.write("  Symbols in range:\n")
                for addr, symbol in symbols.items():
                    if start <= addr <= end:
                        f.write(f"    {symbol} (0x{addr:08X})\n")
        
        print(f"Results written to {output_file}")
        
        # Print simple statistics to console
        print("\nStatistics:")
        print(f"Total symbols found: {len(symbols)}")
        print(f"Total files/splits: {len(set(splits.keys()))}")
        
    except Exception as e:
        print(f"Error writing to output file: {e}")
