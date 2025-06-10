cmake_minimum_required(VERSION 3.10)
project(grinder_backend)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# Disable -Wvariadic-macros warning
add_compile_options(-Wno-variadic-macros)
add_compile_options(-Wno-c99-extensions)
add_compile_options(-Wno-gnu-statement-expression-from-macro-expansion)

# Define ULAPI for userspace program
add_definitions(-DULAPI)

# Add LinuxCNC include directories
include_directories(
    /usr/include/linuxcnc
)

# Define module directory
set(LINUXCNC_MODULE_DIR "/usr/lib/linuxcnc/modules" CACHE PATH "Path to LinuxCNC modules")
set(LINUXCNC_LIB_DIR "/usr/lib/" CACHE PATH "Path to LinuxCNC libraries")
set(LINUXCNC_INCLUDE_DIR "/usr/include/linuxcnc" CACHE PATH "Path to LinuxCNC headers")

# Find system libraries
find_library(LINUXCNC_LIB NAMES linuxcnc PATHS ${LINUXCNC_LIB_DIR})
find_library(NML_LIB NAMES nml PATHS ${LINUXCNC_LIB_DIR})
find_library(HAL_LIB NAMES linuxcnchal PATHS ${LINUXCNC_LIB_DIR} ${LINUXCNC_LIB_DIR}/hallib)

message(STATUS "Using HAL_MODULE: ${HAL_MODULE}")
message(STATUS "Using LINUXCNC_LIB: ${LINUXCNC_LIB}")
message(STATUS "Using NML_LIB: ${NML_LIB}")
message(STATUS "Using HAL_LIB: ${HAL_LIB}")
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

add_executable(grinder_backend grinder-backend.cxx shcom.cc main.cxx settings.cxx backward.cpp)

# Add module directory to link directories
link_directories(${LINUXCNC_MODULE_DIR})

include(FetchContent)
set(DOWNLOAD_EXTRACT_TIMESTAMP TRUE)
FetchContent_Declare(json DOWNLOAD_EXTRACT_TIMESTAMP URL https://github.com/nlohmann/json/releases/download/v3.11.3/json.tar.xz)
FetchContent_MakeAvailable(json)

target_include_directories(grinder_backend PRIVATE ${rapidjson_SOURCE_DIR}/include)

include_directories(
    ${LINUXCNC_INCLUDE_DIR}
    /usr/lib/llvm-19/include  # Add libunwind include path
)

target_link_libraries(grinder_backend PUBLIC 
    ${HAL_LIB}
    ${LINUXCNC_LIB}
    ${NML_LIB}
    pthread
    dl
    nlohmann_json::nlohmann_json
    dw
    unwind
)

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
