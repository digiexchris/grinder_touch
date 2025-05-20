cmake_minimum_required(VERSION 3.10)
project(grinder_backend)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

set(RAPIDJSON_BUILD_TESTS OFF)

set(RAPIDJSON_BUILD_EXAMPLES OFF)
set(RAPIDJSON_BUILD_TESTS OFF)

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
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)
# Import libraries
add_library(hal_lib SHARED IMPORTED)
set_target_properties(hal_lib PROPERTIES
    IMPORTED_LOCATION "${HAL_MODULE}"
)

add_executable(grinder_backend grinder-backend.cxx shcom.cc main.cxx settings.cxx)

# Add module directory to link directories
link_directories(${LINUXCNC_MODULE_DIR})

include(FetchContent)
# # Ensure timestamp preservation during extraction
# set(FETCHCONTENT_FULLY_DISCONNECTED OFF)
# set(FETCHCONTENT_UPDATES_DISCONNECTED OFF)
# set(FETCHCONTENT_QUIET OFF)
set(DOWNLOAD_EXTRACT_TIMESTAMP TRUE)
FetchContent_Declare(json URL https://github.com/nlohmann/json/releases/download/v3.11.3/json.tar.xz)
FetchContent_MakeAvailable(json)

target_include_directories(grinder_backend PRIVATE ${rapidjson_SOURCE_DIR}/include)

include_directories(
    /usr/include/linuxcnc
    /usr/lib/llvm-19/include  # Add libunwind include path
)

target_link_libraries(grinder_backend 
    ${HAL_LIB}
    ${LINUXCNC_LIB}
    ${NML_LIB}
    pthread
    dl
    unwind
    nlohmann_json::nlohmann_json
)

# if(LIBUNWIND_FOUND)
#     target_include_directories(${PROJECT_NAME} PRIVATE ${LIBUNWIND_INCLUDE_DIR})
#     target_link_libraries(${PROJECT_NAME} PRIVATE ${LIBUNWIND_LIBRARIES})
# endif()

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
