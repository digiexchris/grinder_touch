# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a LinuxCNC-based surface grinder control system with a Qt6 touch interface. The project includes:

- **C++ Qt6 GUI Application** (`config/cpp/`) - Main touch interface for grinder control
- **Python Backend** (`config/python/`) - **DEPRECATED** - Legacy Python components being phased out
- **HAL Configuration** (`config/*.hal`) - Hardware abstraction layer configuration files
- **LinuxCNC Integration** - Custom G-code subroutines and M-codes for grinder automation

**Note:** The project is transitioning from Python to pure C++ implementation. All UI and backend logic is being consolidated into the C++ Qt6 application.

## Build System

### Prerequisites

Install dependencies on Debian Bookworm:
```bash
sudo apt update
sudo apt install -y qt6-base-dev qt6-tools-dev qt6-base-dev-tools \
                    libqt6core6 libqt6gui6 libqt6widgets6 \
                    cmake build-essential
sudo apt install -y binutils-dev libdw-dev libboost1.81* \
                    libboost1.81-all-dev libunwind libunwind-dev \
                    libunwind-19-dev libunwind-19
```

### Build Commands

**Primary build method (using CMake presets):**
```bash
cd config/cpp
cmake --preset clang-debug
cmake --build --preset clang-debug
```

**Available presets:**
- `clang-debug` - Debug build with clang compiler (x64)
- `arm64-debug` - Debug build for ARM64 architecture 
- `clang-release` - Release build with clang compiler

**Legacy build script (deprecated):**
```bash
cd config/cpp
./build.sh  # No longer recommended
```

### Testing

**Simulate grinder hardware:**
```bash
cd config
./startsim.sh
```

**Test GUI standalone:**
```bash
cd config
./grinder_touch_gui --standalone
```

## Architecture

### Core Components

1. **GrinderMainWindow** (`grinder_gui.hxx/.cxx`) - Main Qt6 GUI class
   - Loads UI from `grinder_touch.ui`
   - Handles user interactions and touch events
   - Manages LinuxCNC communication

2. **Machine** (`linuxcnc/machine.hxx/.cxx`) - LinuxCNC integration
   - NML communication with LinuxCNC
   - Position monitoring and status updates
   - E-stop and power management

3. **Hal** (`linuxcnc/hal.hxx/.cxx`) - Hardware abstraction layer
   - HAL pin management and communication
   - Template-based pin types (HalFloat, HalBit, HalU32)
   - Component registration and lifecycle

4. **Settings** (`settings.hxx/.cxx`) - Configuration management
   - JSON-based settings persistence
   - Qt property system integration
   - Real-time settings updates

5. **Pin System** (`pins.hxx`) - Enumerated pin definitions
   - Axis limits, speeds, enables
   - Grind cycle controls
   - Wheel dressing parameters

### Key Directories

- `config/cpp/` - C++ Qt6 application source (active development)
- `config/python/` - **DEPRECATED** - Legacy Python backend components
- `config/subroutines/` - G-code subroutines for grinder operations
- `config/m_codes/` - Custom M-code implementations
- `config/linuxcnc/` - LinuxCNC integration code (C++ only)

## Development Workflow

### Code Style
- C++20 standard
- Qt6 signal/slot architecture
- RAII for resource management
- Template-based HAL pin system

### Testing Changes
1. Build with CMake presets: `cmake --preset clang-debug && cmake --build --preset clang-debug`
2. Test standalone: `./grinder_touch_gui --standalone`
3. Test with LinuxCNC: `./startsim.sh`

### HAL Configuration
- `grinder-sim.hal` - Simulated hardware configuration
- `grinder-x86.hal` - x86 hardware configuration
- `grinder-arm64.hal` - ARM64 hardware configuration

## LinuxCNC Integration

### INI File Configuration
```ini
[DISPLAY]
DISPLAY = grinder_touch_gui

[RS274NGC]
SUBROUTINE_PATH=subroutines
USER_M_PATH=m_codes
```

**Note:** The `[FLEX]` section is deprecated as the project no longer uses FlexGUI/Python components.

### HAL Component
The application registers as a HAL component named "grinder" with pins for:
- Axis limits and speeds
- Grind cycle control
- Wheel dressing operations
- Position feedback

## UI System

- **UI File**: `grinder_touch.ui` - Qt Designer interface layout
- **Stylesheet**: `touch.qss` - Custom styling for touch interface
- **Target Resolution**: 1920x1200 (designed for touch screens)
- **Widget Access**: Uses `findChild<WidgetType*>("objectName")` pattern

## Settings Management

Settings are stored in JSON format (`grinder_settings.json`) and include:
- Axis limits and speeds
- Grind cycle parameters
- Wheel dressing configuration
- Tool offsets and G-code snippets

The Settings class uses Qt's property system for real-time updates and automatic persistence.