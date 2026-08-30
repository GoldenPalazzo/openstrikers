cmake_minimum_required(VERSION 3.25)
project(openstrikers CXX C)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

add_subdirectory(aurora EXCLUDE_FROM_ALL)

file(GLOB_RECURSE NL_SOURCES CONFIGURE_DEPENDS
    ${CMAKE_SOURCE_DIR}/decomp/src/NL/*.cpp
)

file(GLOB_RECURSE ODE_SOURCES CONFIGURE_DEPENDS
    ${CMAKE_SOURCE_DIR}/decomp/src/ode/*.cpp
)

add_executable(openstrikers
    ${NL_SOURCES}
    # ${ODE_SOURCES}
    # ./decomp/src/Game/AI/Fielder.cpp
    ./temp_main.cpp
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
    aurora::gx
    aurora::main
    aurora::vi
    aurora::card
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
