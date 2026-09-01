cmake_minimum_required(VERSION 3.25)
project(openstrikers CXX C)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

add_subdirectory(aurora EXCLUDE_FROM_ALL)

file(GLOB_RECURSE NL_SOURCES CONFIGURE_DEPENDS
    ${CMAKE_SOURCE_DIR}/decomp/src/NL/*.cpp
)
list(FILTER NL_SOURCES EXCLUDE REGEX ".*/NL/plat/.*")
# was done automatically by decomp/configure.py calling
# decomp/generate_nlfunction_headers.py
file(COPY_FILE
    "${CMAKE_SOURCE_DIR}/decomp/include/NL/detail/nlFunctionPreProcTemplate.h"
    "${CMAKE_SOURCE_DIR}/decomp/include/NL/detail/nlFunction1PreProcTemplate.h"
    ONLY_IF_DIFFERENT
)

file(GLOB_RECURSE ODE_SOURCES CONFIGURE_DEPENDS
    ${CMAKE_SOURCE_DIR}/decomp/src/ode/*.cpp
)
# An header called "Opcode.h" is in a legal grey area in the original decomp.
# Since the only file that uses it is decomp/src/ode/collision_trimesh_internal.h
# I'm disabling it until I'm in trouble
# For more info, check decomp/THIRD_PARTY_NOTICES.md and
# decomp/docs/ode-provenance.md
list(FILTER ODE_SOURCES EXCLUDE REGEX ".*trimesh.*")
# decomp/src/ode/scrapbook.cpp is obsoleted and shouldn't be compiled
list(FILTER ODE_SOURCES EXCLUDE REGEX ".*scrapbook.*")
# same thing for decomp/src/ode/stack.cpp
list(FILTER ODE_SOURCES EXCLUDE REGEX ".*/ode/stack\\.cpp$")

file(GLOB_RECURSE GAME_SOURCES CONFIGURE_DEPENDS
    ${CMAKE_SOURCE_DIR}/decomp/src/Game/*.cpp
)
list(FILTER GAME_SOURCES EXCLUDE REGEX ".*/AI/Scripts/TestCases\\.cpp$")
# these aren't TUs, their fate is to be included in their base .cpp files
list(FILTER GAME_SOURCES EXCLUDE REGEX ".*_interp\\.cpp$")

add_executable(openstrikers
    ${NL_SOURCES}
    ${ODE_SOURCES}
    ${GAME_SOURCES}
    ./compat_shims.cpp
)

target_include_directories(openstrikers PRIVATE
    ./aurora/include
    ./decomp/src/ode
    ./decomp/include
    ./decomp/extern/musyx/include
    ./decomp/src
)

target_link_libraries(openstrikers PRIVATE
    aurora::core
    aurora::os
    aurora::gx
    aurora::main
    aurora::mtx
    aurora::pad
    aurora::vi
    aurora::card
    aurora::dvd
)

target_compile_definitions(openstrikers PRIVATE
    MUSY_TARGET=MUSY_TARGET_PC
    TARGET_PC
    dSINGLE=1
    dIDESINGLE
    dNODEBUG=ON
    dTHREADING_INTF_DISABLED
    dODE_SMStricker_Patch
    HAVE_MALLOC_H=1
    MUSY_VERSION_MAJOR=2
    MUSY_VERSION_MINOR=0
    MUSY_VERSION_PATCH=3
    NDEBUG=1
    __IEEE_LITTLE_ENDIAN
)

target_compile_options(openstrikers PRIVATE
    -fpermissive
    -include ${CMAKE_SOURCE_DIR}/compat_shims.h
    -idirafter ${CMAKE_SOURCE_DIR}/decomp/include/PowerPC_EABI_Support/MSL_C/MSL_Common
)
