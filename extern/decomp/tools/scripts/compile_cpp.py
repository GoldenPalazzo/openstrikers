#!/usr/bin/env python3
"""
Script to compile a single C++ source file and generate both .o and .s files.

Usage: ./compile_cpp.py <source_file.cpp> [output_dir] [mw_version]

The script uses compile_commands.json to find the file, then extracts compiler
version and flags from build.ninja to compile exactly as the build system does.
"""

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path


def find_file_in_compile_commands(source_file: Path, compile_commands_path: Path) -> dict:
    """Find the file entry in compile_commands.json."""
    if not compile_commands_path.exists():
        return None

    try:
        with open(compile_commands_path, 'r') as f:
            compile_commands = json.load(f)

        source_file_abs = source_file.resolve()

        # Try exact match first
        for entry in compile_commands:
            if Path(entry['file']).resolve() == source_file_abs:
                return entry

        # Try relative path match
        source_file_rel = source_file.as_posix()
        for entry in compile_commands:
            entry_file = Path(entry['file'])
            if entry_file.as_posix() == source_file_rel or entry_file.resolve() == source_file_abs:
                return entry

        return None
    except Exception as e:
        print(f"Error reading compile_commands.json: {e}", file=sys.stderr)
        return None


def extract_compiler_info_from_ninja(output_path: Path, build_ninja_path: Path) -> tuple:
    """Extract compiler version and shift_jis flag from build.ninja for a given output path.

    Returns:
        tuple: (mw_version, use_sjis) or (None, None) if not found
    """
    if not build_ninja_path.exists():
        return None, None

    # Convert to relative path for matching
    try:
        output_path_rel = output_path.relative_to(Path.cwd()).as_posix()
    except ValueError:
        output_path_rel = output_path.as_posix()

    try:
        with open(build_ninja_path, 'r') as f:
            content = f.read()

        # Find the build rule for this output file
        # Pattern: build build/G4QE01/src/Game/GameInfo.o: mwcc_sjis src/Game/GameInfo.cpp
        pattern = rf'^build\s+{re.escape(output_path_rel)}:\s+(mwcc_sjis|mwcc)'
        match = re.search(pattern, content, re.MULTILINE)

        if not match:
            return None, None

        # Extract whether sjis is used
        use_sjis = match.group(1) == 'mwcc_sjis'

        # Extract the build rule block (next 30 lines)
        start_pos = match.start()
        block = content[start_pos:start_pos + 2000]  # Look ahead for the mw_version

        # Find mw_version in this block
        mw_version_match = re.search(r'^\s+mw_version\s*=\s*(.+)$', block, re.MULTILINE)
        if mw_version_match:
            mw_version = mw_version_match.group(1).strip()
            return mw_version, use_sjis

        return None, use_sjis
    except Exception as e:
        print(f"Error reading build.ninja: {e}", file=sys.stderr)
        return None, None


def extract_cflags_from_ninja(output_path: Path, build_ninja_path: Path) -> list:
    """Extract cflags from build.ninja for a given output path."""
    if not build_ninja_path.exists():
        return []

    # Convert to relative path for matching
    try:
        output_path_rel = output_path.relative_to(Path.cwd()).as_posix()
    except ValueError:
        output_path_rel = output_path.as_posix()

    try:
        with open(build_ninja_path, 'r') as f:
            lines = f.readlines()

        # Find the build rule
        build_rule_idx = None
        for i, line in enumerate(lines):
            if line.startswith(f'build {output_path_rel}:'):
                build_rule_idx = i
                break

        if build_rule_idx is None:
            return []

        # Find cflags in the next 30 lines
        cflags_lines = []
        in_cflags = False

        for i in range(build_rule_idx, min(build_rule_idx + 30, len(lines))):
            line = lines[i]

            if line.strip().startswith('cflags ='):
                in_cflags = True
                # Extract the first part of the cflags line
                cflags_line = line.split('cflags =', 1)[1].strip()
                if cflags_line:
                    cflags_lines.append(cflags_line)
            elif in_cflags:
                if line.strip().startswith(('mw_version', 'basedir', 'basefile', 'build')):
                    break
                # Continuation lines start with spaces
                if line.startswith('      ') or line.startswith('    '):
                    cflags_lines.append(line.strip())
                elif line.strip() and not line.strip().startswith('$'):
                    # End of continuation
                    break

        if not cflags_lines:
            return []

        # Join all cflags lines and remove $ continuation markers
        cflags_str = ' '.join(cflags_lines).replace('$', '').strip()

        # Split into flags, handling quoted strings
        flags = []
        current_flag = []
        in_quotes = False
        quote_char = None

        i = 0
        while i < len(cflags_str):
            char = cflags_str[i]

            if char in ('"', "'") and (i == 0 or cflags_str[i-1] != '\\'):
                if not in_quotes:
                    in_quotes = True
                    quote_char = char
                    current_flag.append(char)
                elif char == quote_char:
                    in_quotes = False
                    quote_char = None
                    current_flag.append(char)
                else:
                    current_flag.append(char)
            elif char == ' ' and not in_quotes:
                if current_flag:
                    flags.append(''.join(current_flag))
                    current_flag = []
            else:
                current_flag.append(char)

            i += 1

        if current_flag:
            flags.append(''.join(current_flag))

        return flags

    except Exception as e:
        print(f"Error extracting cflags from build.ninja: {e}", file=sys.stderr)
        return []


def main():
    parser = argparse.ArgumentParser(
        description='Compile a single C++ source file and generate both .o and .s files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s src/Game/GameInfo.cpp
  %(prog)s src/Game/GameInfo.cpp output/
  %(prog)s src/Game/GameInfo.cpp output/ GC/2.0

Note: This script does not interfere with the project's build directory.
All output files are written to the specified output directory.
        """
    )
    parser.add_argument('source_file', type=Path, help='Source file to compile')
    parser.add_argument('output_dir', type=Path, nargs='?', default=Path('compile_output'),
                       help='Output directory (default: compile_output)')
    parser.add_argument('mw_version', type=str, nargs='?', default=None,
                       help='Compiler version override (e.g., GC/2.0)')

    args = parser.parse_args()

    source_file = args.source_file
    output_dir = args.output_dir
    mw_version_override = args.mw_version

    # Check if source file exists
    if not source_file.exists():
        print(f"Error: Source file '{source_file}' not found", file=sys.stderr)
        sys.exit(1)

    # Resolve paths
    source_file = source_file.resolve()
    project_dir = Path.cwd()
    compile_commands_path = project_dir / 'compile_commands.json'
    build_ninja_path = project_dir / 'build.ninja'

    # Step 1: Look up file in compile_commands.json
    entry = find_file_in_compile_commands(source_file, compile_commands_path)
    output_path = None
    mw_version = None
    use_sjis = False

    if entry:
        # Get output path from compile_commands.json
        output_path = Path(entry['output'])
        print(f"Found file in compile_commands.json: {entry['file']}")
        print(f"Output path: {output_path}")

        # Step 2: Extract compiler version and shift_jis flag from build.ninja
        if build_ninja_path.exists():
            mw_version, use_sjis = extract_compiler_info_from_ninja(output_path, build_ninja_path)
            if mw_version:
                print(f"Detected compiler version: {mw_version}")
                print(f"Detected shift_jis: {use_sjis}")
    else:
        print(f"Warning: File not found in compile_commands.json", file=sys.stderr)

    # Use override if provided, otherwise use detected version, otherwise default
    if mw_version_override:
        mw_version = mw_version_override
        print(f"Using override compiler version: {mw_version}")
    elif not mw_version:
        mw_version = 'GC/2.0'
        print(f"Warning: Could not detect compiler version, using default: {mw_version}", file=sys.stderr)

    # Determine output paths
    # Use a simple flat structure in the output directory to avoid conflicts
    basename = source_file.stem

    # Create output directory structure: output_dir/source_file_name/
    # This keeps it simple and avoids conflicts with project build
    full_output_dir = output_dir / basename
    base_output_path = full_output_dir / basename

    # Create output directory
    full_output_dir.mkdir(parents=True, exist_ok=True)

    # Compiler paths
    compiler = project_dir / 'build' / 'compilers' / mw_version / 'mwcceppc.exe'
    sjiswrap = project_dir / 'build' / 'tools' / 'sjiswrap.exe'
    objdump = project_dir / 'build' / 'binutils' / 'powerpc-eabi-objdump'
    python_cmd = os.environ.get('PYTHON', sys.executable)
    transform_dep = project_dir / 'tools' / 'transform_dep.py'

    # Check if required tools exist
    if not compiler.exists() and not sjiswrap.exists():
        print(f"Error: Compiler not found at {compiler} and sjiswrap not found at {sjiswrap}", file=sys.stderr)
        print("Please run the build system first to download tools", file=sys.stderr)
        sys.exit(1)

    if not objdump.exists():
        print(f"Error: objdump not found at {objdump}", file=sys.stderr)
        print("Please run the build system first to download tools", file=sys.stderr)
        sys.exit(1)

    # Extract compilation flags from build.ninja
    cflags = []
    if build_ninja_path.exists() and output_path:
        cflags = extract_cflags_from_ninja(output_path, build_ninja_path)

    # Use default flags if extraction failed
    if not cflags:
        print("Warning: Could not extract flags from build.ninja, using default flags", file=sys.stderr)
        cflags = [
            '-nowraplines',
            '-proc', 'gekko',
            '-align', 'powerpc',
            '-enum', 'int',
            '-fp', 'hardware',
            '-cwd', 'source',
            '-Cpp_exceptions', 'off',
            '-fp_contract', 'on',
            '-nosyspath',
            '-O4,p',
            '-multibyte',
            '-nodefaults',
            '-inline', 'auto',
            '-pragma', 'cats off',
            '-pragma', 'warn_notinlined off',
            '-RTTI', 'off',
            '-str', 'reuse',
            '-sym', 'on',
            '-use_lmw_stmw', 'on',
            '-i', 'build/G4QE01/include',
            '-DBUILD_VERSION=0',
            '-DVERSION_G4QE01',
            '-DNDEBUG=1',
            '-pool', 'off',
            '-DdNODEBUG=ON',
            '-DdIDESINGLE',
            '-DdSINGLE=1',
            '-DdTHREADING_INTF_DISABLED',
            '-DHAVE_MALLOC_H=1',
            '-DdODE_SMStricker_Patch-DMUSY_VERSION_MAJOR=2',
            '-DMUSY_VERSION_MINOR=0',
            '-DMUSY_VERSION_PATCH=3',
            '-i', 'include',
            '-i', 'include/PowerPC_EABI_Support/MSL_C/MSL_Common/',
            '-i', 'src/ode',
            '-i', 'extern/musyx/include',
            '-I-',
            '-i', 'include',
            '-i', 'build/G4QE01/include',
            '-lang=c++',
            '-MMD',
            '-c',
        ]

    # Build compiler command exactly as build.ninja does
    # Format: wine build/tools/sjiswrap.exe build/compilers/$mw_version/mwcceppc.exe $cflags -MMD -c $in -o $basedir
    # Note: -o takes a DIRECTORY, not a file path! MWCC outputs the .o file with the source filename
    
    # Use relative paths (as build.ninja does) - run from project root
    compiler_rel = compiler.relative_to(project_dir) if compiler.is_relative_to(project_dir) else compiler
    sjiswrap_rel = sjiswrap.relative_to(project_dir) if sjiswrap.exists() and sjiswrap.is_relative_to(project_dir) else sjiswrap
    source_file_rel = source_file.relative_to(project_dir) if source_file.is_relative_to(project_dir) else source_file
    basedir_rel = full_output_dir.relative_to(project_dir) if full_output_dir.is_relative_to(project_dir) else full_output_dir

    compiler_cmd = ['wine']
    if use_sjis and sjiswrap.exists():
        compiler_cmd.extend([str(sjiswrap_rel), str(compiler_rel)])
        print(f"Using sjiswrap (Shift-JIS conversion required)")
    else:
        compiler_cmd.append(str(compiler_rel))
        if use_sjis and not sjiswrap.exists():
            print(f"Warning: sjiswrap not found but build.ninja indicates it's needed", file=sys.stderr)

    # Add cflags, then -MMD -c source_file -o basedir (exactly as build.ninja)
    compiler_cmd.extend(cflags)
    compiler_cmd.extend(['-MMD', '-c', str(source_file_rel), '-o', str(basedir_rel)])

    print(f"\nCompiling {source_file.name}...")
    print(f"Output directory: {full_output_dir}")
    print(f"Compiler version: {mw_version}")
    print(f"Note: Output will be written to {full_output_dir}, not the project build directory")
    print()

    # Compile - run from project root (as build.ninja does)
    try:
        result = subprocess.run(compiler_cmd, check=True, capture_output=True, text=True,
                               cwd=str(project_dir))
    except subprocess.CalledProcessError as e:
        # Combine stdout and stderr for error checking
        error_output = (e.stdout or '') + (e.stderr or '')

        # If sjiswrap failed with encoding errors, try without it
        if use_sjis and sjiswrap.exists() and ('Shift JIS encoding errors' in error_output or 'sjiswrap' in error_output.lower()):
            print(f"sjiswrap failed, trying without sjiswrap...", file=sys.stderr)
            compiler_cmd_fallback = ['wine', str(compiler_rel)]
            compiler_cmd_fallback.extend(cflags)
            compiler_cmd_fallback.extend(['-MMD', '-c', str(source_file_rel), '-o', str(basedir_rel)])
            try:
                result = subprocess.run(compiler_cmd_fallback, check=True, capture_output=True, text=True,
                                       cwd=str(project_dir))
                print("Compilation succeeded without sjiswrap")
            except subprocess.CalledProcessError as e2:
                error_output2 = (e2.stdout or '') + (e2.stderr or '')
                print(f"Compilation failed even without sjiswrap:", file=sys.stderr)
                print(error_output2, file=sys.stderr)
                sys.exit(1)
        else:
            print(f"Compilation failed:", file=sys.stderr)
            print(error_output, file=sys.stderr)
            sys.exit(1)

    # Transform dependency file if it exists (as build.ninja does)
    # MWCC outputs a .d file with the same name as the source file
    dep_file_base = full_output_dir / basename
    dep_file = dep_file_base.with_suffix('.d')
    if dep_file.exists() and transform_dep.exists():
        try:
            subprocess.run([python_cmd, str(transform_dep), str(dep_file), str(dep_file)],
                         check=False, capture_output=True)
        except Exception:
            pass  # Ignore errors in dependency transformation

    # MWCC outputs .o file with the same name as the source file in the basedir
    obj_file = full_output_dir / f"{basename}.o"
    if not obj_file.exists():
        # Try alternative: MWCC might output with different naming
        obj_file = full_output_dir / f"{source_file.name}.o"
        if not obj_file.exists():
            print(f"Error: Object file not found in {full_output_dir}", file=sys.stderr)
            print(f"Expected: {basename}.o or {source_file.name}.o", file=sys.stderr)
            sys.exit(1)

    print(f"Generated: {obj_file}")

    # Generate assembly file using dtk elf disasm (same format as build system)
    # This produces the same format as dtk dol split (with .fn directives, address comments, etc.)
    # but with section offsets instead of final ROM addresses
    if obj_file.exists():
        print("Generating assembly file...")
        
        asm_file = full_output_dir / f"{basename}.s"
        dtk = project_dir / 'build' / 'tools' / 'dtk'
        
        if not dtk.exists():
            print(f"Warning: dtk not found at {dtk}, falling back to objdump", file=sys.stderr)
            # Fallback to objdump if dtk is not available
            try:
                result = subprocess.run([str(objdump), '-d', '-S', '-C', str(obj_file)],
                                      check=True, capture_output=True, text=True)
                with open(asm_file, 'w') as f:
                    f.write(result.stdout)
            except subprocess.CalledProcessError:
                result = subprocess.run([str(objdump), '-d', '-C', str(obj_file)],
                                      check=True, capture_output=True, text=True)
                with open(asm_file, 'w') as f:
                    f.write(result.stdout)
        else:
            # Use dtk elf disasm to generate the same format as build system
            try:
                subprocess.run([str(dtk), 'elf', 'disasm', str(obj_file), str(asm_file)],
                             check=True, capture_output=True)
            except subprocess.CalledProcessError as e:
                print(f"Error: dtk elf disasm failed: {e}", file=sys.stderr)
                print(f"Output: {e.stdout.decode() if e.stdout else ''}", file=sys.stderr)
                print(f"Error: {e.stderr.decode() if e.stderr else ''}", file=sys.stderr)
                sys.exit(1)

        print(f"Generated: {asm_file}")
    else:
        print("Error: Object file not created, cannot generate assembly", file=sys.stderr)
        sys.exit(1)

    print()
    print("Success! Generated:")
    print(f"  - {obj_file}")
    print(f"  - {asm_file}")


if __name__ == '__main__':
    main()
