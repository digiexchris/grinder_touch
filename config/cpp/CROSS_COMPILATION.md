# ARM64 Cross-Compilation Setup with schroot

This document explains how to set up ARM64 cross-compilation for the grinder_touch project using `schroot` and `debootstrap` to create a proper ARM64 build environment.

## Overview

The schroot method creates a complete ARM64 Debian environment that allows us to:

- Install ARM64 packages natively within the chroot
- Access LinuxCNC ARM64 packages that aren't available as cross-compilation packages
- Maintain a clean, isolated build environment
- Use QEMU emulation for ARM64 binaries when needed

## Setup Process

1. **Run the installation script:**

   ```bash
   chmod +x install-cross-deps.sh
   ./install-cross-deps.sh
   ```

2. **What the script does:**
   - Installs `schroot`, `debootstrap`, `qemu-user-static`, and `binfmt-support`
   - Creates an ARM64 chroot environment at `/srv/chroot/arm64-bookworm`
   - Configures schroot for the ARM64 environment
   - Installs LinuxCNC ARM64 packages inside the chroot
   - Creates CMake toolchain file (`arm64-toolchain.cmake`)
   - Sets up environment variables script (`~/arm64-cross-env.sh`)

## Directory Structure

```
/srv/chroot/arm64-bookworm/    # ARM64 chroot environment
├── usr/lib/aarch64-linux-gnu/ # ARM64 libraries
├── usr/include/               # ARM64 headers
└── usr/bin/qemu-aarch64-static # QEMU emulator for ARM64

/home/chris/grinder_touch/config/cpp/
├── arm64-toolchain.cmake      # CMake toolchain for cross-compilation
└── ~/arm64-cross-env.sh       # Environment setup script
```

## Usage

### Method 1: CMake Presets (Recommended)

```bash
# Build ARM64 debug version
cmake --preset arm64-debug
cmake --build build/clang-debug-arm64

# Build ARM64 release version  
cmake --preset arm64-release
cmake --build build/clang-release-arm64
```

### Method 2: Manual Environment Setup

```bash
# Source the environment
source ~/arm64-cross-env.sh

# Configure and build manually
mkdir -p build/arm64-manual
cd build/arm64-manual
cmake -DCMAKE_TOOLCHAIN_FILE=../../arm64-toolchain.cmake ../..
make
```

### Method 3: Working Inside the Chroot

```bash
# Enter the ARM64 chroot environment
schroot -c arm64-bookworm

# Inside chroot, you can build natively for ARM64
cd /path/to/project
mkdir build && cd build
cmake ..
make
```

## Key Components

### schroot Configuration

- **Config file:** `/etc/schroot/chroot.d/arm64-bookworm.conf`
- **Chroot path:** `/srv/chroot/arm64-bookworm`
- **User access:** Configured for current user

### CMake Toolchain (`arm64-toolchain.cmake`)

- Sets up Clang cross-compilation for aarch64-linux-gnu
- Configures sysroot to point to the chroot environment
- Sets up pkg-config for ARM64 libraries

### Environment Variables

- `CC/CXX`: Clang compilers with ARM64 target
- `PKG_CONFIG_PATH`: Points to ARM64 library configs
- `CMAKE_SYSROOT`: Points to the chroot environment

## Advantages of schroot Method

1. **Complete Environment:** Full ARM64 Debian environment with all dependencies
2. **Package Management:** Can install ARM64 packages using apt within chroot
3. **LinuxCNC Support:** Access to ARM64 LinuxCNC packages not available for cross-compilation
4. **Isolation:** Clean separation from host system
5. **QEMU Integration:** Transparent ARM64 binary execution via QEMU
6. **Flexibility:** Can work both inside chroot or cross-compile from host

## Troubleshooting

### Check chroot status

```bash
schroot -l
```

### Enter chroot for debugging

```bash
schroot -c arm64-bookworm -u root
```

### Verify ARM64 packages in chroot

```bash
schroot -c arm64-bookworm -- dpkg -l | grep linuxcnc
```

### Check cross-compilation toolchain

```bash
clang-19 --target=aarch64-linux-gnu --sysroot=/srv/chroot/arm64-bookworm -v
```

## File Output

The build process creates binaries with architecture-specific suffixes:

- **x86-64:** `grinder_backend-x64`
- **ARM64:** `grinder_backend-arm64`

Both binaries are built using Clang with optimized settings for their respective target architectures.
