cmake_minimum_required(VERSION 3.25)
project(openstrikers CXX C)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(EXTERN_DIR "${CMAKE_SOURCE_DIR}/extern")
set(SRC_DIR "${CMAKE_SOURCE_DIR}/src")
set(INCLUDE_DIR "${CMAKE_SOURCE_DIR}/include")

add_subdirectory(${EXTERN_DIR}/aurora EXCLUDE_FROM_ALL)

file(GLOB_RECURSE NL_SOURCES CONFIGURE_DEPENDS
    ${EXTERN_DIR}/decomp/src/NL/*.cpp
)
# was done automatically by decomp/configure.py calling
# decomp/generate_nlfunction_headers.py
file(COPY_FILE
    "${EXTERN_DIR}/decomp/include/NL/detail/nlFunctionPreProcTemplate.h"
    "${EXTERN_DIR}/decomp/include/NL/detail/nlFunction1PreProcTemplate.h"
    ONLY_IF_DIFFERENT
)

file(GLOB_RECURSE ODE_SOURCES CONFIGURE_DEPENDS
    ${EXTERN_DIR}/decomp/src/ode/*.cpp
    ${EXTERN_DIR}/decomp/src/ode/*.c
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
list(FILTER ODE_SOURCES EXCLUDE REGEX ".*_orig\\.(cpp|c)$")
set_source_files_properties(
    ${ODE_SOURCES}
    PROPERTIES LANGUAGE CXX
)

file(GLOB_RECURSE GAME_SOURCES CONFIGURE_DEPENDS
    ${EXTERN_DIR}/decomp/src/Game/*.cpp
)
list(FILTER GAME_SOURCES EXCLUDE REGEX ".*/AI/Scripts/TestCases\\.cpp$")
# these aren't TUs, their fate is to be included in their base .cpp files
list(FILTER GAME_SOURCES EXCLUDE REGEX ".*_interp\\.cpp$")
list(FILTER GAME_SOURCES EXCLUDE REGEX ".*FloatingPointExceptions\\.cpp$")
list(FILTER GAME_SOURCES EXCLUDE REGEX ".*CallStackDumper\\.cpp$")

add_executable(openstrikers
    ${NL_SOURCES}
    ${ODE_SOURCES}
    ${GAME_SOURCES}
    ${SRC_DIR}/compat_shims.cpp
    ${SRC_DIR}/main.cpp
)

target_include_directories(openstrikers PRIVATE
    ${INCLUDE_DIR}
    ${EXTERN_DIR}/aurora/include
    ${EXTERN_DIR}/decomp/src/ode
    ${EXTERN_DIR}/decomp/include
    ${EXTERN_DIR}/decomp/src
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
    GOLDEN_DISABLE_AUDIO
)

target_compile_options(openstrikers PRIVATE
    -fpermissive
    -include ${INCLUDE_DIR}/compat_shims.h
    -idirafter ${EXTERN_DIR}/decomp/include/PowerPC_EABI_Support/MSL_C/MSL_Common
)
