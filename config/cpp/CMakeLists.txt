cmake_minimum_required(VERSION 3.10)
project(grinder_backend)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

set(CMAKE_EXPORT_COMPILE_COMMANDS ON)


# Define ULAPI for userspace program
add_definitions(-DULAPI)

# Handle cross-compilation paths
if(CMAKE_CROSSCOMPILING)
    # For cross-compilation, use the sysroot paths
    set(LINUXCNC_INCLUDE_DIR ${CMAKE_SYSROOT}/usr/include/linuxcnc)
    set(LINUXCNC_MODULE_DIR ${CMAKE_SYSROOT}/usr/lib/linuxcnc/modules)
    set(LINUXCNC_LIB_DIR ${CMAKE_SYSROOT}/usr/lib/)
else()
    # For native compilation, use system paths
    set(LINUXCNC_INCLUDE_DIR /usr/include/linuxcnc)
    set(LINUXCNC_MODULE_DIR /usr/lib/linuxcnc/modules)
    set(LINUXCNC_LIB_DIR /usr/lib/)
endif()

# Add LinuxCNC include directories
include_directories(${LINUXCNC_INCLUDE_DIR})

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

add_executable(grinder_backend grinder-backend.cxx shcom.cc main.cxx settings.cxx backward.cpp)

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

# FetchContent_Declare(
#     backward
#     SYSTEM
#     GIT_REPOSITORY https://github.com/bombela/backward-cpp.git
#     GIT_TAG master # or whatever version/tag you prefer
    
# )
# FetchContent_MakeAvailable(backward)

# add_definitions(
#     -BACKWARD_SHARED=0
# )

# set(BACKWARD_SHARED OFF)

target_include_directories(grinder_backend PRIVATE ${rapidjson_SOURCE_DIR}/include)

include_directories(
    ${LINUXCNC_INCLUDE_DIR}
)

# Handle libunwind include path for cross-compilation
if(CMAKE_CROSSCOMPILING)
    # For cross-compilation, try to find libunwind in the sysroot
    find_path(LIBUNWIND_INCLUDE_DIR libunwind.h 
        PATHS ${CMAKE_SYSROOT}/usr/include
        NO_DEFAULT_PATH)
    if(LIBUNWIND_INCLUDE_DIR)
        include_directories(${LIBUNWIND_INCLUDE_DIR})
    endif()
else()
    # For native compilation, use system paths
    include_directories(/usr/lib/llvm-19/include)
endif()

target_link_libraries(grinder_backend PUBLIC 
    ${HAL_LIB}
    ${LINUXCNC_LIB}
    ${NML_LIB}
    pthread
    dl
    nlohmann_json::nlohmann_json
    dw
    unwind
    # Backward
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

message(STATUS "BINARY_POSTFIX is: '${BINARY_POSTFIX}'")

# Add post-build command to copy binary to config directory
add_custom_command(TARGET grinder_backend POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E copy
        $<TARGET_FILE:grinder_backend>
        ${CMAKE_CURRENT_SOURCE_DIR}/../grinder_backend${BINARY_POSTFIX}
    COMMENT "Copying binary to config directory"
)
