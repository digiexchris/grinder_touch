FROM mcr.microsoft.com/devcontainers/cpp:debian-12

RUN apt-get update \
        && export DEBIAN_FRONTEND=noninteractive \
        && apt-get -y install --no-install-recommends clang-format clangd  \
        qt6-base-dev qt6-tools-dev qt6-base-dev-tools \
                    libqt6core6 libqt6gui6 libqt6widgets6 \
                    cmake build-essential ninja-build \
                    binutils-dev libdw-dev \
                    libunwind-19-dev libunwind-19 wget \
        && apt-get autoremove -y \
        && apt-get clean -y \
        && rm -rf /var/lib/apt/lists/*

COPY linuxcnc.list /etc/apt/sources.list.d/linuxcnc.list
RUN apt-key adv --keyserver keyserver.ubuntu.com --recv-keys EF1B07FEE0EE663E && \
    apt-get update && \
        apt-get install -y linuxcnc-uspace linuxcnc-uspace-dev linuxcnc-uspace-dbgsym \
        && apt-get autoremove -y \
        && apt-get clean -y \
        && rm -rf /var/lib/apt/lists/*

RUN apt-get update && apt-get install -y ccache lld \
        && apt-get autoremove -y \
        && apt-get clean -y \
        && rm -rf /var/lib/apt/lists/*
