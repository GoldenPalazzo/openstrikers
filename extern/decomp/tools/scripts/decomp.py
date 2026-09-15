import sys
import json
import requests
from pathlib import Path

DECOMPME_URL = "http://decomp.tulporium.com"
# DECOMPME_URL = "https://www.decomp.me"

BUILD_DIR = Path("build/G4QE01")
OBJ_DIR = BUILD_DIR / "obj"
SRC_DIR = BUILD_DIR / "src"

if len(sys.argv) < 3:
    print(f"Usage: {sys.argv[0]} <obj_name> <diff_label> [--debug]")
    print(f"  Example: {sys.argv[0]} Powerups Update__11PowerupBaseFf")
    print(f"  Example: {sys.argv[0]} Powerups Update__11PowerupBaseFf --debug  (outputs data.json)")
    sys.exit(1)

# Parse arguments
name = sys.argv[1]
diff_label = sys.argv[2]
debug = "--debug" in sys.argv or "-d" in sys.argv

# Remove .o extension if provided
if name.endswith(".o"):
    name = name[:-2]

# Search for object file
obj_path = None
if "/" in name:
    # If path provided, try direct lookup
    obj_path = OBJ_DIR / f"{name}.o"
    if not obj_path.exists():
        print(f"Error: Object file not found: {obj_path}")
        sys.exit(1)
else:
    # Search recursively for the object file
    pattern = f"**/{name}.o"
    matches = list(OBJ_DIR.glob(pattern))
    if not matches:
        print(f"Error: Object file not found: {pattern}")
        sys.exit(1)
    elif len(matches) > 1:
        print("Error: Multiple object files found:")
        for match in matches:
            print(f"  {match}")
        sys.exit(1)
    else:
        obj_path = matches[0]

# Find corresponding context file
# Get relative path from obj_dir
rel_path = obj_path.relative_to(OBJ_DIR)
ctx_path = SRC_DIR / rel_path.with_suffix(".ctx")

if not ctx_path.exists():
    print(f"Warning: Context file not found: {ctx_path}")
    print("  Continuing without context...")
    context = ""
else:
    print(f"Reading context from: {ctx_path}")
    with open(ctx_path, "r", encoding="utf-8", errors="ignore") as ctx_file:
        context = ctx_file.read()

print(f"Using object file: {obj_path}")

with open(obj_path, "rb") as f:
    data = {
        "platform": "gc_wii",  # change this!
        "compiler": "mwcc_247_92",
        "language": "C++",
        "context": context,
        "source_code": "",
        "compiler_flags": "-nowraplines -proc gekko -align powerpc -enum int -fp hardware -cwd source -Cpp_exceptions off -fp_contract on -nosyspath -O4,p -multibyte -nodefaults -inline auto -pragma \"cats off\" -pragma \"warn_notinlined off\" -RTTI off -str reuse -sym on -use_lmw_stmw on -DBUILD_VERSION=0 -DVERSION_G4QE01 -DNDEBUG=1 -pool off -DdNODEBUG=ON -DdIDESINGLE -DdSINGLE=1 -DdTHREADING_INTF_DISABLED -DHAVE_MALLOC_H=1 -DdODE_SMStricker_Patch-DMUSY_VERSION_MAJOR=2 -DMUSY_VERSION_MINOR=0 -DMUSY_VERSION_PATCH=3 -lang=c++ -inline deferred",
        "diff_flags": json.dumps([
            f"--disassemble={diff_label}"
        ]),
        "diff_label": diff_label,
        # "preset": 175,
        # "libraries": json.dumps([{"name": "directx", "version": "9.0"}]),
    }

    # Debug: output data to JSON file
    if debug:
        with open("data.json", "w", encoding="utf-8") as debug_file:
            json.dump(data, debug_file, indent=2, ensure_ascii=False)
        print("Debug: Data written to data.json")

    files = {
        "target_obj": ("target.o", f),
    }

    res = requests.post(
        f"{DECOMPME_URL}/api/scratch",
        files=files,
        data=data,
    )

    if res.status_code == 201:
        response = res.json()

        slug = response["slug"]
        claim_token = response["claim_token"]

        claim_url = f"{DECOMPME_URL}/scratch/{slug}/claim?token={claim_token}"

        print(f"Claim at: {claim_url}")
    else:
        print(f"res.status_code: {res.status_code})")
        print(res.text)
