# Use an official Ubuntu as a base image
FROM ubuntu:20.04

# Set non-interactive environment for tzdata
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=America/New_York

# Install dependencies
RUN apt-get update && apt-get install -y \
    apt-utils \
    build-essential \
    git \
    cmake \
    libpcap-dev \
    libxml2-dev \
    autoconf \
    automake \
    libtool \
    libudev-dev \
    tzdata \
    pkg-config \
    linux-headers-generic

# Clone the EtherLab repository from GitLab
RUN git clone https://gitlab.com/etherlab.org/ethercat.git /etherlab
WORKDIR /etherlab

# Run the bootstrap script and build EtherLab
RUN ./bootstrap && \
    ./configure --sysconfdir=/etc && \
    make all modules && \
    sudo make modules_install install && \
    sudo depmod

# Define the command to run EtherLab (if necessary)
CMD ["sudo", "systemctl", "start", "ethercat"]
