cmake_minimum_required(VERSION 3.10)
project(grinder_backend)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# Define ULAPI for userspace program
add_definitions(-DULAPI)

# Add LinuxCNC include directories
include_directories(
    /usr/include/linuxcnc
)

# Define module directory
set(LINUXCNC_MODULE_DIR /usr/lib/linuxcnc/modules)
set(LINUXCNC_LIB_DIR /usr/lib/)

# Find system libraries
find_library(LINUXCNC_LIB NAMES linuxcnc PATHS ${LINUXCNC_LIB_DIR})
find_library(NML_LIB NAMES nml PATHS ${LINUXCNC_LIB_DIR})
find_library(HAL_LIB NAMES linuxcnchal PATHS ${LINUXCNC_LIB_DIR})

# Use the full path to hal_lib.so
set(HAL_MODULE "${LINUXCNC_MODULE_DIR}/hal_lib.so")
if(NOT EXISTS ${HAL_MODULE})
    message(FATAL_ERROR "hal_lib.so not found at ${HAL_MODULE}")
endif()

message(STATUS "Using HAL_MODULE: ${HAL_MODULE}")
message(STATUS "Using LINUXCNC_LIB: ${LINUXCNC_LIB}")
message(STATUS "Using NML_LIB: ${NML_LIB}")
message(STATUS "Using HAL_LIB: ${HAL_LIB}")

# Import libraries
add_library(hal_lib SHARED IMPORTED)
set_target_properties(hal_lib PROPERTIES
    IMPORTED_LOCATION "${HAL_MODULE}"
)

add_executable(grinder_backend grinder-backend.cpp shcom.cc)

# Add module directory to link directories
link_directories(${LINUXCNC_MODULE_DIR})

target_link_libraries(grinder_backend 
    ${HAL_LIB}
    ${LINUXCNC_LIB}
    ${NML_LIB}
    pthread
    dl
)

# Set RPATH to include LinuxCNC directories
set_target_properties(grinder_backend PROPERTIES
    BUILD_WITH_INSTALL_RPATH TRUE
    INSTALL_RPATH "${LINUXCNC_MODULE_DIR}:${LINUXCNC_LIB_DIR}"
)

# Add post-build command to copy binary to config directory
add_custom_command(TARGET grinder_backend POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E copy
        $<TARGET_FILE:grinder_backend>
        ${CMAKE_CURRENT_SOURCE_DIR}/..
    COMMENT "Copying binary to config directory"
)
