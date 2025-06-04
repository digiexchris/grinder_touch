#!/bin/bash

# Build script for Grinder Touch GUI

# Set build directory
BUILD_DIR="build"
CMAKE_BUILD_TYPE="Debug"

# Create build directory if it doesn't exist
if [ ! -d "$BUILD_DIR" ]; then
    mkdir -p "$BUILD_DIR"
fi

cd "$BUILD_DIR"

# Configure CMake
echo "Configuring CMake..."
cmake .. -DCMAKE_BUILD_TYPE="$CMAKE_BUILD_TYPE" \
         -DCMAKE_EXPORT_COMPILE_COMMANDS=ON

if [ $? -ne 0 ]; then
    echo "CMake configuration failed!"
    exit 1
fi

# Build the project
echo "Building project..."
make -j$(nproc)

if [ $? -ne 0 ]; then
    echo "Build failed!"
    exit 1
fi

echo "Build completed successfully!"
echo "GUI executable: $BUILD_DIR/grinder_touch_gui"
echo "Backend executable: $BUILD_DIR/grinder_backend"

# Copy UI file to build directory for easier testing
if [ -f "../grinder_touch.ui" ]; then
    cp "../grinder_touch.ui" .
    echo "UI file copied to build directory"
fi

if [ -f "../touch.qss" ]; then
    cp "../touch.qss" .
    echo "QSS file copied to build directory"
fi

echo ""
echo "To run the GUI application:"
echo "cd $BUILD_DIR && ./grinder_touch_gui"
echo ""
echo "To use with LinuxCNC, update your INI file:"
echo "[DISPLAY]"
echo "DISPLAY = /path/to/grinder_touch_gui"
