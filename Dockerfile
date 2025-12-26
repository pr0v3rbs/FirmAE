FROM ubuntu:20.04

ENV DEBIAN_FRONTEND=noninteractive

# Install core dependencies
RUN apt-get update && apt-get install -y \
    sudo \
    git \
    wget \
    curl \
    python3 \
    python3-pip \
    python3-venv \
    build-essential \
    qemu-system \
    qemu-user-static \
    binwalk \
    busybox \
    net-tools \
    iproute2 \
    bridge-utils \
    tcpdump \
    tshark \
    libguestfs-tools \
    libglib2.0-dev \
    libpixman-1-dev \
    zlib1g-dev \
    squashfs-tools \
    p7zip-full \
    unzip \
    vim \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /FirmAE

# Copy FirmAE source
COPY . /FirmAE

# Fix permissions
RUN chmod +x *.sh || true

# Default command
CMD ["/bin/bash"]
