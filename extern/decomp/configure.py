#!/usr/bin/env python3

###
# Generates build files for the project.
# This file also includes the project configuration,
# such as compiler flags and the object matching status.
#
# Usage:
#   python3 configure.py
#   ninja
#
# Append --help to see available options.
###

import argparse
import sys
from pathlib import Path
from typing import Any, Dict, List
from typing import Iterator, Optional

from tools.project import (
    Library,
    Object,
    ProgressCategory,
    ProjectConfig,
    calculate_progress,
    generate_build,
    is_windows,
)

# Game versions
DEFAULT_VERSION = 0
VERSIONS = ["G4QE01", "G4QJ01", "G4QP01"]

parser = argparse.ArgumentParser()
parser.add_argument(
    "mode",
    choices=["configure", "progress"],
    default="configure",
    help="script mode (default: configure)",
    nargs="?",
)
parser.add_argument(
    "-v",
    "--version",
    choices=VERSIONS,
    type=str.upper,
    default=VERSIONS[DEFAULT_VERSION],
    help="version to build",
)
parser.add_argument(
    "--build-dir",
    metavar="DIR",
    type=Path,
    default=Path("build"),
    help="base build directory (default: build)",
)
parser.add_argument(
    "--binutils",
    metavar="BINARY",
    type=Path,
    help="path to binutils (optional)",
)
parser.add_argument(
    "--compilers",
    metavar="DIR",
    type=Path,
    help="path to compilers (optional)",
)
parser.add_argument(
    "--map",
    action="store_true",
    help="generate map file(s)",
)
parser.add_argument(
    "--debug",
    action="store_true",
    help="build with debug info (non-matching)",
)
if not is_windows():
    parser.add_argument(
        "--wrapper",
        metavar="BINARY",
        type=Path,
        help="path to wibo or wine (optional)",
    )
parser.add_argument(
    "--dtk",
    metavar="BINARY | DIR",
    type=Path,
    help="path to decomp-toolkit binary or source (optional)",
)
parser.add_argument(
    "--objdiff",
    metavar="BINARY | DIR",
    type=Path,
    help="path to objdiff-cli binary or source (optional)",
)
parser.add_argument(
    "--sjiswrap",
    metavar="EXE",
    type=Path,
    help="path to sjiswrap.exe (optional)",
)
parser.add_argument(
    "--verbose",
    action="store_true",
    help="print verbose output",
)
parser.add_argument(
    "--non-matching",
    dest="non_matching",
    action="store_true",
    help="builds equivalent (but non-matching) or modded objects",
)
parser.add_argument(
    "--no-progress",
    dest="progress",
    action="store_false",
    help="disable progress calculation",
)
args = parser.parse_args()

config = ProjectConfig()
config.version = str(args.version)
version_num = VERSIONS.index(config.version)

# Apply arguments
config.build_dir = args.build_dir
config.dtk_path = args.dtk
config.objdiff_path = args.objdiff
config.binutils_path = args.binutils
config.compilers_path = args.compilers
config.generate_map = args.map
config.non_matching = args.non_matching
config.sjiswrap_path = args.sjiswrap
config.progress = args.progress

if not is_windows():
    config.wrapper = args.wrapper

# Don't build asm unless we're --non-matching
if not config.non_matching:
    config.asm_dir = None

# Tool versions
config.binutils_tag = "2.42-2"
config.compilers_tag = "20251118"
config.dtk_tag = "v1.8.3"
config.objdiff_tag = "v3.8.0"
config.sjiswrap_tag = "v1.2.2"
config.wibo_tag = "1.0.3"

# Project
config.config_path = Path("config") / config.version / "config.yml"
config.check_sha_path = Path("config") / config.version / "build.sha1"
config.asflags = [
    "-mgekko",
    "--strip-local-absolute",
    "-I include",
    "-I src",
    f"-I {config.build_dir}/{config.version}/include",
    f"--defsym BUILD_VERSION={version_num}",
]
config.ldflags = [
    "-fp hardware",
    "-nodefaults",
    "-warn off",
]
if args.debug:
    config.ldflags.append("-g")  # Or -gdwarf-2 for Wii linkers
if args.map:
    config.ldflags.append("-mapunused")
    # config.ldflags.append("-listclosure") # For Wii linkers

# Use for any additional files that should cause a re-configure when modified
config.reconfig_deps = []

nlfunction_template = Path("include/NL/detail/nlFunctionPreProcTemplate.h")
nlfunction_generated_headers = [
    config.build_dir / config.version / "include/NL/detail/nlFunction1PreProcTemplate.h",
]
config.custom_build_rules = [
    {
        "name": "generate_nlfunction_headers",
        "command": "$python tools/generate_nlfunction_headers.py $in $out",
        "description": "GEN $out",
        "restat": True,
    }
]
config.custom_build_steps = {
    "pre-compile": [
        {
            "outputs": nlfunction_generated_headers,
            "rule": "generate_nlfunction_headers",
            "inputs": nlfunction_template,
            "implicit": Path("tools/generate_nlfunction_headers.py"),
        }
    ]
}

# Progress
config.progress_use_fancy = True
config.progress_code_fancy_frac = 250
config.progress_code_fancy_item = "Fans in the Stadium"
config.progress_data_fancy_frac = 90
config.progress_data_fancy_item = "Megastrikes"

# Optional numeric ID for decomp.me preset
# Can be overridden in libraries or objects
config.scratch_preset_id = None

# Base flags, common to most GC/Wii games.
# Generally leave untouched, with overrides added below.

cflags_base = [
    "-nowraplines",
    "-proc gekko",
    "-align powerpc",
    "-enum int",
    "-fp hardware",
    "-cwd source",
    "-Cpp_exceptions off",
    "-fp_contract on",
    "-nosyspath",
    "-O4,p",
    "-multibyte",
    "-nodefaults",
    '-pragma "cats off"',
    '-pragma "warn_notinlined off"',
    "-RTTI off",
    "-str reuse",
    "-sym on",
    "-use_lmw_stmw on",
    f"-i {config.build_dir}/{config.version}/include",
    f"-DBUILD_VERSION={version_num}",
    f"-DVERSION_{config.version}",
    '-pragma "supress_warnings on"',
]

# Debug flags
if args.debug:
    # Or -sym dwarf-2 for Wii compilers
    cflags_base.extend(["-sym on", "-DDEBUG=1"])
else:
    cflags_base.append("-DNDEBUG=1")

# Metrowerks library flags
cflags_runtime = [
    *cflags_base,
    "-use_lmw_stmw on",
    "-str reuse,readonly",
    # "-gccinc",
    "-common off",
    "-inline auto",
]

cflags_runtime_MSL_C = [
    "-nodefaults",
    "-proc gekko",
    "-align powerpc",
    "-enum int",
    "-fp hardware",
    "-Cpp_exceptions off",
    "-O4,p",
    "-inline auto, deferred",
    "-maxerrors 1",
    "-nosyspath",
    "-fp_contract off",
    "-use_lmw_stmw on",
    "-multibyte",
    '-pragma "cats off"',
    '-pragma "warn_notinlined off"',
    "-RTTI off",
    "-char signed",
    "-use_lmw_stmw on",
    "-str reuse,pool,readonly",
    "-common off",
    f"-i {config.build_dir}/{config.version}/include",
    f"-DBUILD_VERSION={version_num}",
    f"-DVERSION_{config.version}",
]

cflags_dolphin = [
    "-nodefaults",
    "-proc gekko",
    "-align powerpc",
    "-enum int",
    "-fp hardware",
    "-Cpp_exceptions off",
    '-pragma "cats off"',
    '-pragma "warn_notinlined off"',
    "-maxerrors 1",
    "-nosyspath",
    "-char signed",
    # "-O4,p",
    "-sym on",
    "-inline auto",
    f"-DVERSION={version_num}",
    f"-DVERSION_{config.version}",
    "-D__GEKKO__",
    "-DSDK_REVISION=1",
]

cflags_ode = [
    "-nodefaults",
    "-proc gekko",
    "-align powerpc",
    "-enum int",
    "-fp hardware",
    "-Cpp_exceptions off",
    "-O4,p",
    # "-inline off",
    "-inline auto, deferred",
    "-maxerrors 1",
    "-nosyspath",
    "-fp_contract on",
    "-multibyte",
    '-pragma "cats off"',
    '-pragma "warn_notinlined off"',
    "-RTTI off",
    "-char signed",
    "-use_lmw_stmw on",
    # "-str reuse,pool,readonly",
    "-common off",
    "-cwd source",
    "-str reuse",
    "-sym on"
]

cflags_musyx = [
    "-proc gekko",
    "-nodefaults",
    "-nosyspath",
    "-i include",
    "-i extern/musyx/include",
    "-inline auto,depth=4",
    "-O4,p",
    "-fp hard",
    "-enum int",
    "-sym on",
    "-Cpp_exceptions off",
    "-str reuse,pool,readonly",
    "-fp_contract off",
    "-DMUSY_TARGET=MUSY_TARGET_DOLPHIN",
]

cflags_musyx_debug = [
    "-proc gecko",
    "-fp hard",
    "-nodefaults",
    "-nosyspath",
    "-i include",
    "-i extern/musyx/include",
    "-g",
    "-sym on",
    "-D_DEBUG=1",
    "-fp hard",
    "-enum int",
    "-Cpp_exceptions off",
    "-DMUSY_TARGET=MUSY_TARGET_DOLPHIN",
]

cflags_nl = [
    *cflags_base,
    "-proc gekko",
    "-nodefaults",
    "-nosyspath",
    "-i include",
]

cflags_odemuexi = [
    *cflags_base,
    "-inline deferred"
]

cflags_trk_minnow_dolphin = [
    *cflags_base,
    "-use_lmw_stmw on",
    "-rostr",
    "-str reuse",
    "-gccinc",
    "-common off",
    "-inline deferred",
    "-char signed",
    "-sdata 0",
    "-sdata2 0",   
    "-sdatathreshold 0",
]

includes_base = [
    "include",
    # "include/libc",
    "include/PowerPC_EABI_Support/MSL_C/MSL_Common/", #instead of libc, which is a copy of it...
]

system_includes_base = [
    "include",
    f"{config.build_dir}/{config.version}/include",
]

config.linker_version = "GC/1.3.2"

Objects = List[Object]


def Lib(
    lib_name: str,
    objects: Objects,
    mw_version: str = config.linker_version,
    cflags=cflags_base,
    fix_epilogue=True,
    fix_trk=False,
    includes: List[str] = includes_base,
    system_includes: List[str] = system_includes_base,
    src_dir: Optional[str] = None,
    category: Optional[str] = None,
) -> Library:
    def make_includes(includes: List[str]) -> Iterator[str]:
        return map(lambda s: f"-i {s}", includes)

    lib = {
        "lib": lib_name,
        # "mw_version": f"GC/1.2.5{'n' if fix_epilogue else ''}",
        "mw_version": mw_version, 
        "cflags": [
            *cflags,
            *make_includes(includes),
            "-I-",
            *make_includes(system_includes),
        ],
        "host": False,
        "progress_category": category,
        "objects": objects,
    }

    if src_dir is not None:
        lib["src_dir"] = src_dir

    return lib


def RuntimeLib(lib_name: str, objects: Objects) -> Library:
    return Lib(
        lib_name,
        objects,
        cflags=cflags_runtime,
        fix_epilogue=False,
        category="runtime",
    )


def RuntimeLib_MSL_C(lib_name: str, objects: Objects) -> Library:
    return Lib(
        lib_name,
        objects,
        mw_version="GC/2.5",
        cflags=[
            *cflags_runtime_MSL_C,
            "-fp_contract on", 
            "-inline auto,deferred", 
            "-str pool,readonly"
        ],
        category="runtime",
    )

def NLLib(lib_name: str, objects: Objects) -> Library:
    return Lib(
        lib_name,
        objects,
        includes=[
            *includes_base,
            "src/ode",
            "extern/musyx/include",
        ],
        system_includes=[
            *system_includes_base,
        ],
        mw_version="GC/2.0",
        # mw_version="GC/1.3.2",
        # mw_version="GC/1.2.5n",
        cflags=[
            *cflags_base,
            "-pool off",
            "-DdNODEBUG=ON",
            "-DdIDESINGLE",
            "-DdSINGLE=1",
            "-DdTHREADING_INTF_DISABLED",
            "-DHAVE_MALLOC_H=1",
            "-DdODE_SMStricker_Patch"
        ],            
        category="game",
    )

def GameLib(lib_name: str, objects: Objects) -> Library:
    return Lib(
        lib_name,
        objects,
        includes=[
            *includes_base,
            "src/ode",
            "extern/musyx/include",
        ],
        system_includes=[
            *system_includes_base,
        ],
        mw_version="GC/2.6",
        cflags=[
            *cflags_base,
            "-pool off",
            "-DdNODEBUG=ON",
            "-DdIDESINGLE",
            "-DdSINGLE=1",
            "-DdTHREADING_INTF_DISABLED",
            "-DHAVE_MALLOC_H=1",
            "-DdODE_SMStricker_Patch",
            "-DMUSY_VERSION_MAJOR=2",
            "-DMUSY_VERSION_MINOR=0",
            "-DMUSY_VERSION_PATCH=3",
        ],
        category="game",
    )


def ODELib(lib_name: str, objects: Objects, cflags=cflags_ode) -> Library:
    return Lib(
        lib_name,
        objects,
        includes=[
            # Internal ODE headers (src/ode/objects.h, obstack.h, array.h) share
            # basenames with the public API copies under include/ode. Source files
            # directly in src/ode/ pick up the internal versions via -cwd source,
            # but files in src/ode/ext/ miss the cwd lookup and would otherwise
            # resolve the public include/ode/objects.h (no struct defs). List
            # src/ode first so the internal headers win for all ODE objects.
            "src/ode",
            *includes_base,
            "include/ode",
        ],
        system_includes=[
            *system_includes_base,
            "include/PowerPC_EABI_Support/MSL_C++/MSL_Common/",
        ],
        mw_version="GC/2.0",
        cflags=[
            *cflags,
            "-DdNODEBUG=ON",
            "-DdIDESINGLE",
            "-DdSINGLE=1",
            "-DdTHREADING_INTF_DISABLED",
            "-DHAVE_MALLOC_H=1",
        ],        
        category="ode",
    )


def DolphinLib_O3(lib_name: str, objects: Objects, cflags=cflags_dolphin) -> Library:
    return Lib (
        lib_name,
        objects,
        includes=[
            *includes_base,
            "src/Dolphin",
        ],
        system_includes=[
            *system_includes_base,
            "include/dolphin",
        ],
        mw_version="GC/1.2.5n",
        cflags=[
            *cflags,
            "-O3,p",
        ],        
        category="sdk",
    )

def DolphinLib(lib_name: str, objects: Objects, cflags=cflags_dolphin) -> Library:
    return Lib (
        lib_name,
        objects,
        includes=[
            *includes_base,
            "src/Dolphin",
        ],
        system_includes=[
            *system_includes_base,
            "include/dolphin",
        ],
        mw_version="GC/1.2.5n",
        # mw_version="GC/1.3.2",
        cflags=[
            *cflags,
            "-O4,p",
        ],        
        category="sdk",
    )

def DolphinLib132(lib_name: str, objects: Objects, cflags=cflags_dolphin) -> Library:
    return Lib (
        lib_name,
        objects,
        includes=[
            *includes_base,
            "src/Dolphin",
        ],
        system_includes=[
            *system_includes_base,
            "include/dolphin",
        ],
        # mw_version="GC/1.2.5n",
        mw_version="GC/1.3.2",
        cflags=[
            *cflags,
            "-O4,p",
        ],        
        category="sdk",
    )


def DolphinTrkLib(lib_name: str, objects: Objects, cflags=cflags_trk_minnow_dolphin) -> Library:
    src_dir = None
    includes = includes_base
    system_includes = system_includes_base
    return Lib(
        lib_name,
        objects,
        mw_version="GC/1.3.2",
        src_dir=src_dir,
        cflags=cflags,
        includes=includes,
        system_includes=system_includes,
        category="sdk",
    )

def MusyxLib(lib_name: str, objects: Objects, debug=False, major=2, minor=0, patch=3) -> Library:
    cflags = cflags_musyx if not debug else cflags_musyx_debug
    return Lib (
        lib_name,
        objects,
        src_dir="extern/musyx/src",
        includes=[
            *includes_base,
            "src/Dolphin",
        ],
        mw_version="GC/1.3.2",

        cflags=[
            *cflags,
            f"-DMUSY_VERSION_MAJOR={major}",
            f"-DMUSY_VERSION_MINOR={minor}",
            f"-DMUSY_VERSION_PATCH={patch}",
        ],
        category="musyx",
    )


Matching = True                   # Object matches and should be linked
NonMatching = False               # Object does not match and should not be linked
Equivalent = config.non_matching  # Object should be linked when configured with --non-matching


# Object is only matching for specific versions
def MatchingFor(*versions):
    return config.version in versions


config.warn_missing_config = True
config.warn_missing_source = False


config.libs = [
    RuntimeLib(
        "Runtime.PPCEABI.H",
        [
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "PowerPC_EABI_Support/Runtime/__init_cpp_exceptions.cpp", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "PowerPC_EABI_Support/Runtime/__mem.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "PowerPC_EABI_Support/Runtime/__va_arg.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "PowerPC_EABI_Support/Runtime/global_destructor_chain.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "PowerPC_EABI_Support/Runtime/ptmf.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "PowerPC_EABI_Support/Runtime/runtime.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "PowerPC_EABI_Support/Runtime/Gecko_ExceptionPPC.cpp", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "PowerPC_EABI_Support/Runtime/NMWException.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "PowerPC_EABI_Support/Runtime/GCN_mem_alloc.c", extra_cflags=["-inline auto"]),
        ],
    ),
    RuntimeLib_MSL_C(
        "MSL_C.PPCEABI.bare.H",
        [
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "PowerPC_EABI_Support/MSL/MSL_C/MSL_Common/extras.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "PowerPC_EABI_Support/MSL/MSL_C/MSL_Common/alloc.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "PowerPC_EABI_Support/MSL/MSL_C/MSL_Common/ansi_files.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "PowerPC_EABI_Support/MSL/MSL_C/MSL_Common/abort_exit.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "PowerPC_EABI_Support/MSL/MSL_C/MSL_Common/errno.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "PowerPC_EABI_Support/MSL/MSL_C/MSL_Common/ansi_fp.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "PowerPC_EABI_Support/MSL/MSL_C/MSL_Common/arith.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "PowerPC_EABI_Support/MSL/MSL_C/MSL_Common/buffer_io.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "PowerPC_EABI_Support/MSL/MSL_C/MSL_Common/ctype.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "PowerPC_EABI_Support/MSL/MSL_C/MSL_Common/locale.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "PowerPC_EABI_Support/MSL/MSL_C/MSL_Common/direct_io.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "PowerPC_EABI_Support/MSL/MSL_C/MSL_Common/mbstring.c", extra_cflags=["-inline auto", "-inline noauto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "PowerPC_EABI_Support/MSL/MSL_C/MSL_Common/mem.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "PowerPC_EABI_Support/MSL/MSL_C/MSL_Common/mem_funcs.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "PowerPC_EABI_Support/MSL/MSL_C/MSL_Common/misc_io.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "PowerPC_EABI_Support/MSL/MSL_C/MSL_Common/printf.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "PowerPC_EABI_Support/MSL/MSL_C/MSL_Common/scanf.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "PowerPC_EABI_Support/MSL/MSL_C/MSL_Common/string.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "PowerPC_EABI_Support/MSL/MSL_C/MSL_Common/strtold.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "PowerPC_EABI_Support/MSL/MSL_C/MSL_Common/strtoul.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "PowerPC_EABI_Support/MSL/MSL_C/MSL_Common/char_io.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "PowerPC_EABI_Support/MSL/MSL_C/MSL_Common/wchar_io.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "PowerPC_EABI_Support/MSL/MSL_C/MSL_Common/float.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "PowerPC_EABI_Support/MSL/MSL_C/MSL_Common/signal.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "PowerPC_EABI_Support/MSL/MSL_C/MSL_Common/file_io.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "PowerPC_EABI_Support/MSL/MSL_C/MSL_Common/file_pos.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "PowerPC_EABI_Support/MSL/MSL_C/MSL_Common/qsort.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "PowerPC_EABI_Support/MSL/MSL_C/MSL_Common/wctype.c", extra_cflags=["-inline auto"]),

            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "PowerPC_EABI_Support/MSL/MSL_C/MSL_Common/wcstoul.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "PowerPC_EABI_Support/MSL/MSL_C/MSL_Common/wscanf.c", extra_cflags=["-inline auto"]),

            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "PowerPC_EABI_Support/MSL/MSL_C/MSL_Common/e_acos.c", extra_cflags=["-inline auto", "-inline off"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "PowerPC_EABI_Support/MSL/MSL_C/MSL_Common/e_fmod.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "PowerPC_EABI_Support/MSL/MSL_C/MSL_Common/e_pow.c", extra_cflags=["-inline auto", "-inline off"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "PowerPC_EABI_Support/MSL/MSL_C/MSL_Common/e_rem_pio2.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "PowerPC_EABI_Support/MSL/MSL_C/MSL_Common/k_cos.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "PowerPC_EABI_Support/MSL/MSL_C/MSL_Common/k_rem_pio2.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "PowerPC_EABI_Support/MSL/MSL_C/MSL_Common/k_sin.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "PowerPC_EABI_Support/MSL/MSL_C/MSL_Common/k_tan.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "PowerPC_EABI_Support/MSL/MSL_C/MSL_Common/s_atan.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "PowerPC_EABI_Support/MSL/MSL_C/MSL_Common/s_ceil.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "PowerPC_EABI_Support/MSL/MSL_C/MSL_Common/s_copysign.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "PowerPC_EABI_Support/MSL/MSL_C/MSL_Common/s_floor.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "PowerPC_EABI_Support/MSL/MSL_C/MSL_Common/s_frexp.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "PowerPC_EABI_Support/MSL/MSL_C/MSL_Common/s_ldexp.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "PowerPC_EABI_Support/MSL/MSL_C/MSL_Common/s_modf.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "PowerPC_EABI_Support/MSL/MSL_C/MSL_Common/s_sin.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "PowerPC_EABI_Support/MSL/MSL_C/MSL_Common/s_tan.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "PowerPC_EABI_Support/MSL/MSL_C/MSL_Common/w_acos.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "PowerPC_EABI_Support/MSL/MSL_C/MSL_Common/w_fmod.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "PowerPC_EABI_Support/MSL/MSL_C/MSL_Common/w_pow.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "PowerPC_EABI_Support/MSL/MSL_C/MSL_Common/e_sqrt.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "PowerPC_EABI_Support/MSL/MSL_C/MSL_Common/w_sqrt.c", extra_cflags=["-inline auto"]),

            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "PowerPC_EABI_Support/MSL/MSL_C/PPC_EABI/uart_console_io_gcn.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "PowerPC_EABI_Support/MSL/MSL_C/PPC_EABI/critical_regions.gamecube.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "PowerPC_EABI_Support/MSL/MSL_C/PPC_EABI/math_ppc.c", extra_cflags=["-inline auto"]),
        ],
    ),
    GameLib(
        "SMS (Super Mario Strikers)",
        [
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/main.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/ComUpdateTask.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/FrontEndTask.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/GameRenderTask.cpp", extra_cflags=["-inline auto", "-inline deferred"]),

            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/Sys/clock.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/Sys/debug.cpp", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/Sys/simpleparser.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/Sys/eventman.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/Sys/geventdst.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/Sys/tweak.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/Sys/FloatingPointExceptions.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/Sys/CallStackDumper.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/Core/mtRandom.cpp", extra_cflags=["-inline auto", "-inline deferred"]),

            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/Sys/PlatStream.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/Sys/GCStream.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/Sys/movie.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/Sys/THPSimple.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/Sys/gcmemcard.cpp", extra_cflags=["-inline auto", "-inline deferred"]),

            # Game Objects
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/Game.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/GameInfo.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/GameTweaks.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/CharacterTweaks.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/ScriptTuning.cpp", extra_cflags=["-inline auto", "-inline auto,deferred"]),

            # Game/Transitions
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/Transitions/ScreenTransitionManager.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/Transitions/ColourBlendScreenTransition.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/Transitions/ScriptedTransition.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/Transitions/TransLight.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/Transitions/TransitionSequence.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/Transitions/ModelTransition.cpp", extra_cflags=["-inline auto", "-inline deferred"]),

            # Camera
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/Camera/CameraLoader.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/Camera/CameraMan.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/Camera/FaceCam.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/Camera/GoalCam.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/Camera/ShootToScoreCam.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/Camera/TopDownCamera.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/Camera/kickoffcam.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/Camera/MatrixEffectCam.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/Camera/FollowCam.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/Camera/ReplayCamera.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/Camera/AnimViewerCam.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/Camera/rumblefilter.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/Camera/DebugCam.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/Camera/GameplayCam.cpp", extra_cflags=["-inline auto", "-inline deferred"], mw_version="GC/1.3"),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/Camera/animcam.cpp", extra_cflags=["-inline auto", "-inline deferred"]),

            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/Replay.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/ReplayChoreo.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/ReplayManager.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/RenderSnapshot.cpp", extra_cflags=["-inline auto", "-inline deferred"]),

            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/Ball.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/Net.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/Field.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/Character.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/CharacterTemplate.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/CharacterEffects.cpp", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/Player.cpp", extra_cflags=["-inline auto", "-inline deferred"]),

            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/Goalie.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/GoalieFatigue.cpp", extra_cflags=["-inline auto", "-inline deferred"]),

            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/Team.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/Formation.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/FormationDefines.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/TweaksBase.cpp", extra_cflags=["-inline auto"]),

            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/NisPlayer.cpp", extra_cflags=["-inline auto", "-inline deferred"]),

            # Game Render
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/Render/FlareHandler.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/Render/Nis.cpp", extra_cflags=["-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/Render/CameraGuy.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/Render/SkinAnimatedNPC.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/Render/depthoffield.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/Render/Wiper.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/Render/Bowser.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/Render/ChainChomp.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/Render/GraphicsLoader.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/Render/Indicators.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/Render/ShootToScoreArrow.cpp", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/Render/ShootToScoreMeter.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/Render/Jumbotron.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/Render/SkinAnimatedMovableNPC.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/Render/NPCManager.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/Render/SidelineExplodable.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/Render/ElectricFence.cpp", extra_cflags=["-inline auto", "-inline deferred"]),

            # related to character (should probably be in Game/Render)
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/PoseNode.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/PoseAccumulator.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SHierarchy.cpp", extra_cflags=["-inline auto", "-inline deferred"]),

            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SAnim.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SAnim/AnimRetargeter.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SAnim/pnSAnimController.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SAnim/pnBlender.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SAnim/pnSingleAxisBlender.cpp", extra_cflags=["-inline auto", "-inline deferred"], mw_version="GC/1.3.2"),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SAnim/pnFeather.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/AnimInventory.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/Blinker.cpp", extra_cflags=["-inline auto"]),

            # Net 
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/Render/NetMesh.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/NetMeshEdge.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/NetMeshModelLoader.cpp", extra_cflags=["-inline auto", "-inline deferred"]),

            # Terrain / Environment
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/TrophyInfo.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/TerrainTypes.cpp", extra_cflags=["-inline auto"]),

            # Audio
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/Audio/CharacterAudio.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/Audio/GameAudio.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/Audio/audio.cpp", extra_cflags=["-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/Audio/SebringSoundDefines.cpp" , extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/Audio/SoundEventScript.cpp" , extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/Audio/WorldAudio.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/Audio/AudioEventHandler.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/Audio/AudioLoader.cpp", mw_version="GC/1.3.2", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/Audio/AudioScriptEventMgr.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/Audio/AudioStream.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/Audio/CrowdMood.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/Audio/StreamTrack.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/Audio/PriorityStream.cpp", extra_cflags=["-inline auto", "-inline deferred"]),

            # Physics
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/Physics.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/RayCollider.cpp", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/PhysicsAIBall.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/Physics/PhysicsBox.cpp", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/PhysicsShell.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/Physics/PhysicsColumn.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/Physics/PhysicsCapsule.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/PhysicsFakeBall.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/Physics/PhysicsBall.cpp", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/PhysicsSphere.cpp", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/Physics/PhysicsFinitePlane.cpp", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/Physics/PhysicsGroundPlane.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/Physics/PhysicsPlane.cpp", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/Physics/PhysicsRoundedCorner.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/Physics/PhysicsWall.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/PhysicsNPC.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/PhysicsObject.cpp", extra_cflags=["-inline noauto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/PhysicsCompositeObject.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/Physics/PhysicsCharacterBase.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/Physics/PhysicsCharacter.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/Physics/CollisionSpace.cpp" , extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/PhysicsTransform.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/Physics/PhysicsWorld.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/Physics/LoadablePhysicsMesh.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/Physics/CharacterPhysicsElement.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/Physics/PhysicsNet.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/Physics/PhysicsBanana.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/Physics/PhysicsGoalie.cpp", extra_cflags=["-inline auto", "-inline deferred"]),

            # World
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/world.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/WorldManager.cpp", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/BasicStadium.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/World/WorldLoader.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/World/worldanim.cpp", extra_cflags=["-inline auto", "-inline deferred"]),

            # Pad
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/Pad/FlickDetection.cpp", extra_cflags=["-inline auto", "-inline deferred"]),

            # Tasks
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/WorldUpdateTask.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/ParticleUpdateTask.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/TweakerTask.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/TestTask.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/ProfileTask.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/PlatPadUpdateTask.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/FixedUpdateTask.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/DispatchEventsTask.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/ResetTask.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/TransitionTask.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/BeginFrameTask.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/EndFrameTask.cpp", extra_cflags=["-inline auto", "-inline deferred"]),

            # Triggers
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/Triggers/BinaryTriggerFile.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/MarioTriggers.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/WorldTriggers.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/CharacterTriggers.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/Triggers/AnimTagScript.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/Triggers/AnimTrigger.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/Triggers/SebringAnimScript.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            

            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/PadMonkey.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/PadActions.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/RumbleActions.cpp", extra_cflags=["-inline auto", "-inline deferred"]),

            # Render
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/Render/Presentation.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/Render/CrowdManager.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/Render/NPCLoader.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/Render/RenderShadow.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/Render/StaticModelExplodable.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/Render/AnimatedModelExplodable.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/GameObjectLighting.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/Font/fontmanager.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            
            # AI
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/AI/AILoader.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/AI/AIPlay.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/AI/AiUtil.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/AI/Powerups.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/AI/AISandbox.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/AI/HeadTrack.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/AIPad.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/AI/DecisionEntity.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/AI/ScriptAction.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/AI/FilteredRandom.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/AI/ShotMeter.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/AI/AvoidController.cpp", extra_cflags=["-inline auto", "-inline deferred", "-msext on"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/AI/Fielder.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/AI/FielderDesires.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/AI/FielderActions.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/AI/Fuzzy.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/AI/FuzzyVariant.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/AI/GoalieActions.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/AI/GoalieLooseBall.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/AI/GoalieSave.cpp", extra_cflags=["-inline auto", "-inline deferred", "-msext on"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/AI/Scripts/CommonScript.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/AI/SpaceSearch.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/AI/Variant.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/AI/Scripts/FormationScript.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/AI/Scripts/ScriptCaching.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/AI/Scripts/ScriptQuestions.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/AI/Scripts/Plays/DefaultDefensive.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/AI/Scripts/Plays/DefaultOffensive.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/AI/Scripts/Plays/DefaultLoose.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/AI/Scripts/RootScript.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/AI/Scripts/ScriptDefines.cpp", extra_cflags=["-inline auto", "-inline deferred"]),

            # Frontend / Scenes
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/FE/GameSceneManager.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/FE/BaseSceneHandler.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/FE/BaseGameSceneManager.cpp", extra_cflags=["-inline auto", "-inline deferred"]),

            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/OverlayManager.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/FE/Overlay/OverlayHandlerHUD.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/FE/Overlay/OverlayHandlerInGameText.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/FE/Overlay/OverlayHandlerSTSX2.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/FE/Overlay/OverlayHandlerDemo.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/FE/Overlay/OverlayHandlerGoal.cpp", extra_cflags=["-inline auto", "-inline deferred"]),

            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/FE/feTweenFuncs.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/FE/feOptionsSubMenus.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/FE/feScene.cpp", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/FE/feRender.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/FE/feFontResource.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/FE/feSceneResource.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/FE/fePackage.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/FE/feSoundKeyframeTrigger.cpp", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/FE/feTextureResource.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/FE/feScrollText.cpp", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/FE/feAsyncImage.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/FE/feAnimation.cpp", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/FE/FELoader.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/FE/feNSNMessenger.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/FE/fePopupMenu.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/FE/feManager.cpp", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/FE/feCaptainComponent.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/FE/feTweener.cpp", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/FE/feSceneManager.cpp", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/FE/feLibObject.cpp", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/FE/feChooseSideComponent.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/FE/feAnimModelManager.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/FE/feButtonComponent.cpp", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/FE/feSidekickGridComponent.cpp", extra_cflags=["-inline noauto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/FE/FEAudio.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/FE/fePresentation.cpp", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/FE/feMapMenu.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/FE/feResourceManager.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/FE/feCaptainGridComponent.cpp", extra_cflags=["-inline noauto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/FE/feInput.cpp", extra_cflags=["-inline auto", "-inline deferred", "-msext on"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/FE/feScrollingTicker.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/FE/feMusic.cpp", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/FE/feInGameMessengerManager.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/FE/feHelpFuncs.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/FE/feSlideMenu.cpp", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/FE/LidOpenMessage.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/FE/BraggingRights.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/FE/Cup/CupTickerManager.cpp", extra_cflags=["-inline auto", "-inline deferred", '-pragma "inline_max_total_size(5120)"'],),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/FE/Overlay/OverlayHandlerSummary.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/FE/Overlay/OverlayHandlerWinner.cpp", extra_cflags=["-inline auto", "-inline deferred"]),

            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/FE/tlSlide.cpp", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/FE/tlComponent.cpp", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/FE/tlInstance.cpp", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/FE/tlComponentInstance.cpp", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/FE/tlTextInstance.cpp", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/FE/tlTextInstance_runtime.cpp", extra_cflags=["-inline auto"]),

            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SH/SHBackground.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SH/SHChooseCaptains.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SH/SHChooseCup.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SH/SHChooseSides.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SH/SHCredits.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SH/SHCrossFader.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SH/SHCupCheater.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SH/SHCupChooseCaptain.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SH/SHCupHub.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SH/SHCupOptions.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SH/SHCupTrophy.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SH/SHHealthWarning.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SH/SHLesson.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SH/SHLessonSelect.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SH/SHLoading.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SH/SHLoadingTransition.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SH/SHMainMenu.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SH/SHMilestoneTrophy.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SH/SHMoviePlayer.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SH/SHOptions.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SH/SHPause.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SH/SHPauseOptions.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SH/SHPausePostGame.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SH/SHProgressiveScan.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SH/SHQuickGameplayOptions.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SH/SHSaveLoad.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SH/SHSkillSelect.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SH/SHSpoils.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SH/SHStadiumSelect.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SH/SHSuperTeam.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SH/SHTitleScreen.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SH/SHTournSetParams.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SH/SHTournTeamSetup.cpp", extra_cflags=["-inline auto", "-inline deferred"]),

            # GFX
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/Drawable/DrawableModel.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/Drawable/DrawableNetMesh.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/Drawable/DrawableCharacter.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/Drawable/DrawableBall.cpp", extra_cflags=["-inline auto", "-msext on"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/Drawable/DrawablePowerup.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/Drawable/DrawableExplosionFragment.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/Drawable/DrawableObj.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/Drawable/DrawableTmModel.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/Drawable/DrawableSkinModel.cpp", extra_cflags=["-inline auto"]),


            # Interpreter
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/InterpreterCore.cpp", extra_cflags=["-inline auto", "-inline deferred"]),

            # GL
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/GL/GLMaterial.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/GL/GLTextureAnim.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/GL/GLVertexAnim.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/GL/GLMeshWriter.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/GL/GLInventory.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/GL/GLRenderBuffer.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/GL/GLSkinMesh.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/GL/gluMeshWriter.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/GL/gluSkinMesh.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/GL/ShaderSkinMesh.cpp", extra_cflags=["-inline auto", "-inline deferred"]),

            # FX
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/objectblur.cpp", extra_cflags=["-inline auto"]),

            # AnimProps
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/AnimProps/globalanimproperties.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/AnimProps/goalieanimproperties.cpp", extra_cflags=["-inline auto", "-inline deferred"]),

            # SoundProps
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SoundProps/birdogensoundproperties.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SoundProps/birdograsssoundproperties.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SoundProps/birdoconcretesoundproperties.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SoundProps/birdometalsoundproperties.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SoundProps/birdorubbersoundproperties.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SoundProps/birdowoodsoundproperties.cpp", extra_cflags=["-inline auto", "-inline deferred"]),

            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SoundProps/bowsergensoundproperties.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SoundProps/bowsergrasssoundproperties.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SoundProps/bowserconcretesoundproperties.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SoundProps/bowsermetalsoundproperties.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SoundProps/bowserrubbersoundproperties.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SoundProps/bowserwoodsoundproperties.cpp", extra_cflags=["-inline auto", "-inline deferred"]),

            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SoundProps/crittergensoundproperties.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SoundProps/crittergrasssoundproperties.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SoundProps/critterconcretesoundproperties.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SoundProps/crittermetalsoundproperties.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SoundProps/critterrubbersoundproperties.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SoundProps/critterwoodsoundproperties.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SoundProps/critterrobotsoundproperties.cpp", extra_cflags=["-inline auto", "-inline deferred"]),

            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SoundProps/daisygensoundproperties.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SoundProps/daisygrasssoundproperties.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SoundProps/daisyconcretesoundproperties.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SoundProps/daisymetalsoundproperties.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SoundProps/daisyrubbersoundproperties.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SoundProps/daisywoodsoundproperties.cpp", extra_cflags=["-inline auto", "-inline deferred"]),

            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SoundProps/dkgensoundproperties.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SoundProps/dkgrasssoundproperties.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SoundProps/dkconcretesoundproperties.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SoundProps/dkmetalsoundproperties.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SoundProps/dkrubbersoundproperties.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SoundProps/dkwoodsoundproperties.cpp", extra_cflags=["-inline auto", "-inline deferred"]),

            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SoundProps/hambrosgensoundproperties.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SoundProps/hambrosgrasssoundproperties.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SoundProps/hambrosconcretesoundproperties.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SoundProps/hambrosmetalsoundproperties.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SoundProps/hambrosrubbersoundproperties.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SoundProps/hambroswoodsoundproperties.cpp", extra_cflags=["-inline auto", "-inline deferred"]),

            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SoundProps/koopagensoundproperties.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SoundProps/koopagrasssoundproperties.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SoundProps/koopaconcretesoundproperties.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SoundProps/koopametalsoundproperties.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SoundProps/kooparubbersoundproperties.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SoundProps/koopawoodsoundproperties.cpp", extra_cflags=["-inline auto", "-inline deferred"]),

            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SoundProps/luigigensoundproperties.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SoundProps/luigigrasssoundproperties.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SoundProps/luigiconcretesoundproperties.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SoundProps/luigimetalsoundproperties.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SoundProps/luigirubbersoundproperties.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SoundProps/luigiwoodsoundproperties.cpp", extra_cflags=["-inline auto", "-inline deferred"]),

            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SoundProps/mariogensoundproperties.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SoundProps/mariograsssoundproperties.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SoundProps/marioconcretesoundproperties.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SoundProps/mariometalsoundproperties.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SoundProps/mariorubbersoundproperties.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SoundProps/mariowoodsoundproperties.cpp", extra_cflags=["-inline auto", "-inline deferred"]),

            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SoundProps/peachgensoundproperties.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SoundProps/peachgrasssoundproperties.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SoundProps/peachmetalsoundproperties.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SoundProps/peachconcretesoundproperties.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SoundProps/peachrubbersoundproperties.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SoundProps/peachwoodsoundproperties.cpp", extra_cflags=["-inline auto", "-inline deferred"]),

            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SoundProps/supergensoundproperties.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SoundProps/supergrasssoundproperties.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SoundProps/superconcretesoundproperties.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SoundProps/supermetalsoundproperties.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SoundProps/superrubbersoundproperties.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SoundProps/superwoodsoundproperties.cpp", extra_cflags=["-inline auto", "-inline deferred"]),

            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SoundProps/toadgrasssoundproperties.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SoundProps/toadconcretesoundproperties.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SoundProps/toadwoodsoundproperties.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SoundProps/toadrubbersoundproperties.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SoundProps/toadmetalsoundproperties.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SoundProps/toadgensoundproperties.cpp", extra_cflags=["-inline auto", "-inline deferred"]),

            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SoundProps/waluigiconcretesoundproperties.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SoundProps/waluigigensoundproperties.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SoundProps/waluigigrasssoundproperties.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SoundProps/waluigimetalsoundproperties.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SoundProps/waluigirubbersoundproperties.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SoundProps/waluigiwoodsoundproperties.cpp", extra_cflags=["-inline auto", "-inline deferred"]),

            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SoundProps/warioconcretesoundproperties.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SoundProps/wariogensoundproperties.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SoundProps/wariograsssoundproperties.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SoundProps/wariometalsoundproperties.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SoundProps/wariorubbersoundproperties.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SoundProps/wariowoodsoundproperties.cpp", extra_cflags=["-inline auto", "-inline deferred"]),

            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SoundProps/yoshiconcretesoundproperties.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SoundProps/yoshigensoundproperties.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SoundProps/yoshigrasssoundproperties.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SoundProps/yoshimetalsoundproperties.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SoundProps/yoshirubbersoundproperties.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SoundProps/yoshiwoodsoundproperties.cpp", extra_cflags=["-inline auto", "-inline deferred"]),

            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SoundProps/stadbattlesoundproperties.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SoundProps/stadbowsersoundproperties.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SoundProps/stadconcretesoundproperties.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SoundProps/stadcratersoundproperties.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SoundProps/stadgensoundproperties.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SoundProps/stadgrasssoundproperties.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SoundProps/stadkongasoundproperties.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SoundProps/stadmetalsoundproperties.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SoundProps/stadpalacesoundproperties.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SoundProps/stadpipesoundproperties.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SoundProps/stadrubbersoundproperties.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SoundProps/stadundersoundproperties.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SoundProps/stadwoodsoundproperties.cpp", extra_cflags=["-inline auto", "-inline deferred"]),

            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SoundProps/crowdsoundproperties.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SoundProps/powerupsoundproperties.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/SoundProps/worldsoundproperties.cpp", extra_cflags=["-inline auto", "-inline deferred"]),

            # Effects
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/Effects/efList.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/Effects/EffectsTemplate.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/Effects/EffectsGroup.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/Effects/ParticleSystem.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/Effects/EmissionController.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/Effects/EmissionManager.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/Effects/PhotoFlashEffect.cpp", extra_cflags=["-inline auto", "-inline deferred"]),

            # DB
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/DB/SaveLoad.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/DB/UserOptions.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/DB/StatsTracker.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/DB/Simmer.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/DB/CustomTournament.cpp", extra_cflags=["-inline auto", "-inline deferred"]),

            # Debug
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/Debug/FrameCounter.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/Debug/ShapeRender.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/Debug/TimeRegions.cpp", extra_cflags=["-inline auto", "-inline deferred"]),

            # Loader
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/Loader/LoadingManager.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
        ],
    ),
    GameLib(
        "NL (Next Level Library)",
        [
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "NL/nlBind.cpp", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "NL/nlAVLTree.cpp", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "NL/nlBundleFile.cpp", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "NL/nlConfig.cpp", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "NL/nlDebug.cpp", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "NL/nlDebugFile.cpp", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "NL/nlEndian.cpp", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "NL/nlFile.cpp", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "NL/nlFileGC.cpp", extra_cflags=["-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "NL/nlFont.cpp", extra_cflags=["-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "NL/nlLocalization.cpp", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "NL/nlMain.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "NL/nlMath.cpp", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "NL/MemAlloc.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "NL/nlMemory.cpp", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "NL/nlPrint.cpp", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "NL/nlSlotPool.cpp", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "NL/nlString.cpp", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "NL/nlTask.cpp", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "NL/nlTextBox.cpp", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "NL/nlTextEscape.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "NL/nlTicker.cpp", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "NL/nlTimer.cpp", extra_cflags=["-inline auto"]),

            # Ext/Platform
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "NL/plat/globalpad.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "NL/plat/platpad.cpp", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "NL/plat/platvmath.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "NL/plat/platqmath.cpp", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "NL/plat/plataudio.cpp", extra_cflags=["-inline auto"]),

            # Ext/GC
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "NL/gc/gcSwizzler.cpp", extra_cflags=["-inline auto", "-inline deferred"]),

            # Ext/Game-Specific?
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Game/AI/StatsGatherer.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "NL/math.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "NL/utility.cpp", extra_cflags=["-inline auto", "-inline deferred"]),

            # Ext/GL
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "NL/glx/glxSwap.cpp", extra_cflags=["-inline noauto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "NL/glx/glxFont.cpp", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "NL/glx/glxMatrix.cpp", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "NL/glx/glxMemory.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "NL/glx/glxTexture.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "NL/glx/glxSend.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "NL/glx/glxLoadModel.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "NL/glx/glxGX.cpp", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "NL/glx/glxDisplayList.cpp", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "NL/glx/glxTarget.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "NL/gl/gl.cpp", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "NL/gl/glDraw2.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "NL/gl/glDraw3.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "NL/gl/glFont.cpp", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "NL/gl/glMatrix.cpp", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "NL/gl/glMatrixStack.cpp", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "NL/gl/glMemory.cpp", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "NL/gl/glModify.cpp", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "NL/gl/glRenderList.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "NL/gl/glStat.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "NL/gl/glState.cpp", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "NL/gl/glStruct.cpp", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "NL/gl/glTarget.cpp", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "NL/gl/glView.cpp", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "NL/gl/glUserData.cpp", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "NL/gl/glModel.cpp", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "NL/gl/glTexture.cpp", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "NL/gl/glConstant.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "NL/gl/glAppAttach.cpp", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "NL/gl/glPlat.cpp", extra_cflags=["-inline auto"]),
        ],
    ),

    ODELib(
        "Open Dynamics Engine (ODE)",
        [
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "ode/NLGAdditions.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "ode/collision_kernel.cpp", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "ode/collision_space.cpp", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "ode/collision_std.cpp", extra_cflags=["-inline auto", "-fp_contract on"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "ode/collision_transform.cpp", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "ode/collision_util.cpp", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "ode/error.cpp", extra_cflags=["-inline auto", "-inline off"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "ode/joint.cpp", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "ode/memory.cpp", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "ode/ode.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "ode/matrix.cpp", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "ode/mass.cpp", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "ode/obstack.cpp", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "ode/quickstep.cpp", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "ode/rotation.cpp", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "ode/util.cpp", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "ode/ext/dColumn.cpp", extra_cflags=["-inline auto", "-inline off"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "ode/ext/dFinitePlane.cpp", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "ode/ext/dRoundedCorner.cpp", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "ode/odemath.cpp", extra_cflags=["-inline auto", "-inline deferred"]),
        ],
    ),
    DolphinLib(
        "THP",
        [
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Dolphin/thp/THPDec.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Dolphin/thp/THPAudio.c", extra_cflags=["-inline auto"]),
        ]
    ),
    DolphinLib_O3(
        "Dolfin SDK",
        [
            # Dolphin/OS
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Dolphin/exi/EXIBios.c", extra_cflags=["-inline auto"]),
        ]
    ),
    DolphinLib(
        "Dolfin SDK",
        [
            # Dolphin/OS
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Dolphin/os/OS.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Dolphin/os/OSAlarm.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Dolphin/os/OSAlloc.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Dolphin/os/OSArena.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Dolphin/os/OSAudioSystem.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Dolphin/os/OSCache.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Dolphin/os/OSContext.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Dolphin/os/OSError.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01"), "Dolphin/os/OSExec.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Dolphin/os/OSFont.c", extra_cflags=["-inline auto", "-char unsigned"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Dolphin/os/OSInterrupt.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Dolphin/os/OSLink.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Dolphin/os/OSMemory.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Dolphin/os/OSMutex.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Dolphin/os/OSReboot.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Dolphin/os/OSReset.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Dolphin/os/OSResetSW.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Dolphin/os/OSRtc.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Dolphin/os/OSSync.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Dolphin/os/OSThread.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Dolphin/os/OSTime.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Dolphin/os/__start.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Dolphin/os/__ppc_eabi_init.cpp", extra_cflags=["-inline auto"]),

            # Dolfin/AI
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Dolphin/ai/ai.c", extra_cflags=["-inline auto"]),
            
            # Dolfin/AR
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Dolphin/ar/ar.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Dolphin/ar/arq.c", extra_cflags=["-inline auto"]),

            # Dolphin/BASE
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Dolphin/base/PPCArch.c", extra_cflags=["-inline auto"]),

            # Dolphin/CARD
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Dolphin/card/CARDBios.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Dolphin/card/CARDUnlock.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Dolphin/card/CARDRdwr.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Dolphin/card/CARDBlock.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Dolphin/card/CARDDir.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Dolphin/card/CARDCheck.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Dolphin/card/CARDMount.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Dolphin/card/CARDFormat.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Dolphin/card/CARDOpen.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Dolphin/card/CARDCreate.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Dolphin/card/CARDRead.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Dolphin/card/CARDWrite.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Dolphin/card/CARDDelete.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Dolphin/card/CARDStat.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Dolphin/card/CARDNet.c", extra_cflags=["-inline auto"]),

            # Dolfin/DB
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Dolphin/db/db.c", extra_cflags=["-inline auto"]),

            # Dolfin/DSP
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Dolphin/dsp/dsp.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Dolphin/dsp/dsp_debug.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Dolphin/dsp/dsp_task.c", extra_cflags=["-inline auto"]),

            # Dolphin/DVD
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Dolphin/dvd/dvdlow.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Dolphin/dvd/dvdfs.c", extra_cflags=["-inline auto"]),
            Object(
                MatchingFor("G4QE01", "G4QJ01", "G4QP01"),
                "Dolphin/dvd/dvd.c",
                source="Dolphin/dvd_2003/dvd.c" if config.version == "G4QP01" else "Dolphin/dvd/dvd.c",
                extra_cflags=["-inline auto"],
            ),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Dolphin/dvd/dvdqueue.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Dolphin/dvd/dvderror.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Dolphin/dvd/dvdidutils.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Dolphin/dvd/dvdFatal.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Dolphin/dvd/fstload.c", extra_cflags=["-inline auto"]),

            # Dolphin/EXI
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Dolphin/exi/EXIUart.c", extra_cflags=["-inline auto"]),

            # Dolphin/GX
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Dolphin/gx/GXInit.c", extra_cflags=["-inline auto", "-opt nopeephole"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Dolphin/gx/GXFifo.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Dolphin/gx/GXAttr.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Dolphin/gx/GXMisc.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Dolphin/gx/GXGeometry.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Dolphin/gx/GXFrameBuf.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Dolphin/gx/GXLight.c", extra_cflags=["-inline auto", "-fp_contract off"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Dolphin/gx/GXTexture.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Dolphin/gx/GXBump.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Dolphin/gx/GXTev.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Dolphin/gx/GXPixel.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Dolphin/gx/GXDisplayList.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Dolphin/gx/GXTransform.c", extra_cflags=["-inline auto", "-fp_contract off"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Dolphin/gx/GXPerf.c", extra_cflags=["-inline auto"]),

            # Dolphin/MTX
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Dolphin/mtx/mtx.c", extra_cflags=["-inline auto", "-char signed"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Dolphin/mtx/mtx44.c", extra_cflags=["-inline auto", "-char signed"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Dolphin/mtx/quat.c", extra_cflags=["-inline auto", "-char signed", "-fp_contract off"]),

            # Dolphin/PAD
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Dolphin/pad/Padclamp.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Dolphin/pad/Pad.c", extra_cflags=["-inline auto"]),

            # Dolphin/SI
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Dolphin/si/SIBios.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Dolphin/si/SISamplingRate.c", extra_cflags=["-inline auto"]),

            # Dolphin/VI
            Object(
                MatchingFor("G4QE01", "G4QJ01", "G4QP01"),
                "Dolphin/vi/vi.c",
                source="Dolphin/vi_2003/vi.c" if config.version == "G4QP01" else "Dolphin/vi/vi.c",
                extra_cflags=["-inline auto"],
            ),
        ],
    ),

    DolphinLib132(
        "VM",
        [
            # Dolphin/vm.a
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Dolphin/vm.a/VM.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Dolphin/vm.a/VMPageReplacement.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Dolphin/vm.a/VMMapping.c", extra_cflags=["-inline auto", "-O4,s"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Dolphin/vm.a/VMBase.c", extra_cflags=["-inline auto"]),
        ],
    ),    


    DolphinLib(
        "amcstubs",
        [
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Dolphin/AmcStub/AmcExi2Stubs.c", extra_cflags=["-inline auto"]),
        ],
    ),    
    DolphinLib(
        "OdemuExi2",
        [
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Dolphin/OdemuExi2/DebuggerDriver.c", extra_cflags=["-inline auto"]),
        ],
        cflags=cflags_odemuexi,
    ),

    DolphinLib(
        "OdenotStub",
        [
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "Dolphin/OdenotStub/odenotstub.c", extra_cflags=["-inline auto"]),
        ],
    ),        
    MusyxLib(
        "Musyx",
        [
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "musyx/runtime/seq.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "musyx/runtime/synth.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "musyx/runtime/seq_api.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "musyx/runtime/snd_synthapi.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "musyx/runtime/stream.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "musyx/runtime/synthdata.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "musyx/runtime/synthmacros.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "musyx/runtime/synthvoice.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "musyx/runtime/synth_ac.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "musyx/runtime/synth_dbtab.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "musyx/runtime/synth_adsr.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "musyx/runtime/synth_vsamples.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "musyx/runtime/s_data.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "musyx/runtime/hw_dspctrl.c",  extra_cflags=["-inline auto", "-sdatathreshold 8"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "musyx/runtime/hw_volconv.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "musyx/runtime/snd3d.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "musyx/runtime/snd_init.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "musyx/runtime/snd_math.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "musyx/runtime/snd_midictrl.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "musyx/runtime/snd_service.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "musyx/runtime/hardware.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "musyx/runtime/dsp_import.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "musyx/runtime/hw_aramdma.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "musyx/runtime/hw_dolphin.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "musyx/runtime/hw_memory.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "musyx/runtime/CheapReverb/creverb_fx.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "musyx/runtime/CheapReverb/creverb.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "musyx/runtime/StdReverb/reverb_fx.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "musyx/runtime/StdReverb/reverb.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "musyx/runtime/Delay/delay_fx.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "musyx/runtime/Chorus/chorus_fx.c", extra_cflags=["-inline auto"]),
        ]
    ),        
    DolphinTrkLib(
        "TRK_MINNOW_DOLPHIN",
        [
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "SDK/TRK_MINNOW_DOLPHIN/main_TRK.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "SDK/TRK_MINNOW_DOLPHIN/mutex_TRK.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "SDK/TRK_MINNOW_DOLPHIN/mem_TRK.c", extra_cflags=["-inline auto"]),

            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "SDK/TRK_MINNOW_DOLPHIN/mpc_7xx_603e.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "SDK/TRK_MINNOW_DOLPHIN/CircleBuffer.c", extra_cflags=["-inline auto"]),

            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "SDK/TRK_MINNOW_DOLPHIN/dolphin_trk.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "SDK/TRK_MINNOW_DOLPHIN/dolphin_trk_glue.c", extra_cflags=["-inline auto"]),
            
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "SDK/TRK_MINNOW_DOLPHIN/target_options.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "SDK/TRK_MINNOW_DOLPHIN/targcont.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "SDK/TRK_MINNOW_DOLPHIN/targsupp.c", extra_cflags=["-inline auto"]),
            
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "SDK/TRK_MINNOW_DOLPHIN/notify.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "SDK/TRK_MINNOW_DOLPHIN/flush_cache.c", extra_cflags=["-inline auto"]),

            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "SDK/TRK_MINNOW_DOLPHIN/dispatch.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "SDK/TRK_MINNOW_DOLPHIN/serpoll.c", extra_cflags=["-inline auto", "-sdata 8"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "SDK/TRK_MINNOW_DOLPHIN/mainloop.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "SDK/TRK_MINNOW_DOLPHIN/nubevent.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "SDK/TRK_MINNOW_DOLPHIN/nubinit.c", extra_cflags=["-inline auto"]),

            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "SDK/TRK_MINNOW_DOLPHIN/usr_put.c", extra_cflags=["-inline auto"]),

            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "SDK/TRK_MINNOW_DOLPHIN/support.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "SDK/TRK_MINNOW_DOLPHIN/UDP_Stubs.c", extra_cflags=["-inline auto"]),

            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "SDK/TRK_MINNOW_DOLPHIN/msg.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "SDK/TRK_MINNOW_DOLPHIN/msgbuf.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "SDK/TRK_MINNOW_DOLPHIN/msghndlr.c", extra_cflags=["-inline auto"]),

            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "SDK/TRK_MINNOW_DOLPHIN/MWTrace.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "SDK/TRK_MINNOW_DOLPHIN/MWCriticalSection_gc.cpp", extra_cflags=["-inline auto"]),

            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "SDK/TRK_MINNOW_DOLPHIN/main.c", extra_cflags=["-inline auto", "-sdatathreshold 8"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "SDK/TRK_MINNOW_DOLPHIN/main_gdev.c", extra_cflags=["-inline auto", "-sdatathreshold 8"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "SDK/TRK_MINNOW_DOLPHIN/__exception.s", extra_cflags=["-inline auto"]),

            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "SDK/TRK_MINNOW_DOLPHIN/targimpl.c", extra_cflags=["-inline auto"]),
            Object(MatchingFor("G4QE01", "G4QJ01", "G4QP01"), "SDK/TRK_MINNOW_DOLPHIN/mslsupp.c", extra_cflags=["-inline auto", "-enum int"]),
        ]
    ),
]


# Optional callback to adjust link order. This can be used to add, remove, or reorder objects.
# This is called once per module, with the module ID and the current link order.
#
# For example, this adds "dummy.c" to the end of the DOL link order if configured with --non-matching.
# "dummy.c" *must* be configured as a Matching (or Equivalent) object in order to be linked.
def link_order_callback(module_id: int, objects: List[str]) -> List[str]:
    # Don't modify the link order for matching builds
    if not config.non_matching:
        return objects
    if module_id == 0:  # DOL
        return objects + ["dummy.c"]
    return objects

# Uncomment to enable the link order callback.
# config.link_order_callback = link_order_callback


# Optional extra categories for progress tracking
# Adjust as desired for your project
config.progress_categories = [
    ProgressCategory("game", "Game Code"),
    ProgressCategory("sdk", "Dolphin SDK Code"),
    ProgressCategory("ode", "ODE (Open Dynamics Engine) (Third Party)"),
    ProgressCategory("musyx", "Musyx (Third Party)"),
    ProgressCategory("runtime", "Gekko Runtime Code"),
]
config.print_progress_categories = args.verbose
config.progress_each_module = args.verbose

# Optional extra arguments to `objdiff-cli report generate`
config.progress_report_args = [
    # Marks relocations as mismatching if the target value is different
    # Default is "functionRelocDiffs=none", which is most lenient
    # "--config functionRelocDiffs=data_value",
]

if args.mode == "configure":
    # Write build.ninja and objdiff.json
    generate_build(config)
elif args.mode == "progress":
    # Print progress information
    calculate_progress(config)
else:
    sys.exit("Unknown mode: " + args.mode)
