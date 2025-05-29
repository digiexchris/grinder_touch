#!/bin/bash
# Install cross-compilation dependencies for Debian 12 with Clang using schroot

set -e  # Exit on any error

CHROOT_NAME="arm64-bookworm"
CHROOT_PATH="/srv/chroot/${CHROOT_NAME}"

echo "Installing schroot and debootstrap tools..."
sudo apt update
sudo apt install -y schroot debootstrap qemu-user-static binfmt-support

echo "Adding ARM64 architecture..."
sudo dpkg --add-architecture arm64

echo "Installing Clang and related tools..."
sudo apt install -y clang llvm lld
sudo apt install -y clang-19 llvm-19 lld-19

echo "Installing build tools..."
sudo apt install -y ninja-build ccache

echo "Installing native LinuxCNC packages..."
# Add LinuxCNC GPG key
sudo apt-key adv --keyserver keyserver.ubuntu.com --recv-keys 3CB9FD148F374FEF || {
    echo "Failed to add GPG key via keyserver, trying alternative method..."
    curl -fsSL https://www.linuxcnc.org/dists/bookworm/Release.gpg | sudo apt-key add -
}

# Add LinuxCNC repository
echo "deb [arch=amd64] https://www.linuxcnc.org/ bookworm 2.9-uspace" | sudo tee /etc/apt/sources.list.d/linuxcnc.list
sudo apt update
sudo apt install -y linuxcnc-uspace linuxcnc-uspace-dev

echo "Creating ARM64 chroot environment..."
# Create chroot directory
sudo mkdir -p "${CHROOT_PATH}"

# Create ARM64 chroot using debootstrap
sudo debootstrap --arch=arm64 --include=build-essential,pkg-config,cmake bookworm "${CHROOT_PATH}" http://deb.debian.org/debian

echo "Configuring schroot for ARM64..."
# Create schroot configuration
sudo tee /etc/schroot/chroot.d/${CHROOT_NAME}.conf << EOF
[${CHROOT_NAME}]
description=Debian 12 ARM64 cross-compilation environment
type=directory
directory=${CHROOT_PATH}
users=$(whoami)
groups=sbuild
root-groups=root
personality=linux
preserve-environment=true
shell=/bin/bash
EOF

echo "Setting up ARM64 chroot environment..."
# Copy qemu static for ARM64 emulation
sudo cp /usr/bin/qemu-aarch64-static "${CHROOT_PATH}/usr/bin/"

# Configure DNS in chroot
echo "nameserver 8.8.8.8" | sudo tee "${CHROOT_PATH}/etc/resolv.conf"

# Update package lists in chroot
sudo schroot -c ${CHROOT_NAME} -u root -- apt update

echo "Installing LinuxCNC in ARM64 chroot..."
# Add LinuxCNC repository to chroot
sudo schroot -c ${CHROOT_NAME} -u root -- /bin/bash -c "
    apt-key adv --keyserver keyserver.ubuntu.com --recv-keys 3CB9FD148F374FEF || \
    curl -fsSL https://www.linuxcnc.org/dists/bookworm/Release.gpg | apt-key add -
    echo 'deb [arch=arm64] https://www.linuxcnc.org/ bookworm 2.9-uspace' > /etc/apt/sources.list.d/linuxcnc.list
    apt update
    apt install -y linuxcnc-uspace-dev libunwind-dev libdw-dev
"

echo "Setting up cross-compilation environment variables..."
# Create environment setup script
tee ~/arm64-cross-env.sh << 'EOF'
#!/bin/bash
# ARM64 cross-compilation environment
export CC="clang-19 --target=aarch64-linux-gnu --sysroot=/srv/chroot/arm64-bookworm"
export CXX="clang++-19 --target=aarch64-linux-gnu --sysroot=/srv/chroot/arm64-bookworm"
export AR="llvm-ar-19"
export STRIP="llvm-strip-19"
export RANLIB="llvm-ranlib-19"
export PKG_CONFIG_PATH="/srv/chroot/arm64-bookworm/usr/lib/aarch64-linux-gnu/pkgconfig:/srv/chroot/arm64-bookworm/usr/lib/pkgconfig"
export PKG_CONFIG_SYSROOT_DIR="/srv/chroot/arm64-bookworm"
export CMAKE_TOOLCHAIN_FILE="$(pwd)/arm64-toolchain.cmake"
EOF

chmod +x ~/arm64-cross-env.sh

echo "Creating CMake toolchain file..."
tee arm64-toolchain.cmake << 'EOF'
# ARM64 cross-compilation toolchain file
set(CMAKE_SYSTEM_NAME Linux)
set(CMAKE_SYSTEM_PROCESSOR aarch64)

set(CMAKE_SYSROOT /srv/chroot/arm64-bookworm)

set(CMAKE_C_COMPILER clang-19)
set(CMAKE_CXX_COMPILER clang++-19)
set(CMAKE_C_COMPILER_TARGET aarch64-linux-gnu)
set(CMAKE_CXX_COMPILER_TARGET aarch64-linux-gnu)

set(CMAKE_FIND_ROOT_PATH /srv/chroot/arm64-bookworm)
set(CMAKE_FIND_ROOT_PATH_MODE_PROGRAM NEVER)
set(CMAKE_FIND_ROOT_PATH_MODE_LIBRARY ONLY)
set(CMAKE_FIND_ROOT_PATH_MODE_INCLUDE ONLY)
set(CMAKE_FIND_ROOT_PATH_MODE_PACKAGE ONLY)

set(PKG_CONFIG_EXECUTABLE /usr/bin/pkg-config)
set(ENV{PKG_CONFIG_PATH} "/srv/chroot/arm64-bookworm/usr/lib/aarch64-linux-gnu/pkgconfig:/srv/chroot/arm64-bookworm/usr/lib/pkgconfig")
set(ENV{PKG_CONFIG_SYSROOT_DIR} "/srv/chroot/arm64-bookworm")
EOF

echo "Cross-compilation environment set up successfully!"
echo ""
echo "Usage:"
echo "1. Source the environment: source ~/arm64-cross-env.sh"
echo "2. Use CMake preset: cmake --preset arm64-debug"
echo "3. Or enter chroot: schroot -c ${CHROOT_NAME}"
echo ""
echo "Chroot environment: ${CHROOT_PATH}"
