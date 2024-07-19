FROM --platform=amd64 ubuntu:22.04
LABEL AUTHOR Mingeun Kim <pr0v3rbs@kaist.ac.kr>, Minkyo Seo <0xsaika@gmail.com>
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y wget gnupg2 && \
    wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - && \
    echo 'deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main' | tee /etc/apt/sources.list.d/google-chrome.list

RUN apt-get update && apt-get install -y apt-utils wget tar bc psmisc ruby telnet \
    socat net-tools iputils-ping iptables iproute2 curl \
    python3 python3-pip python-is-python3 libpq-dev \
    busybox-static bash-static fakeroot git kpartx netcat-openbsd \
    nmap python3-psycopg2 snmp uml-utilities util-linux vlan \
    python3-magic unrar openjdk-8-jdk \
    mtd-utils gzip bzip2 tar arj lhasa p7zip p7zip-full cabextract \
    fusecram cramfsswap squashfs-tools sleuthkit default-jdk cpio \
    lzop lzma srecord zlib1g-dev liblzma-dev liblzo2-dev \
    qemu-system-arm qemu-system-mips qemu-system-x86 qemu-utils \
    google-chrome-stable ntfs-3g postgresql

RUN python3 -m pip install --upgrade pip && \
    python3 -m pip install psycopg2 psycopg2-binary python-lzo cstruct ubi_reader \
    selenium bs4 requests future paramiko pysnmp==4.4.6 pycryptodome

RUN wget https://github.com/ReFirmLabs/binwalk/archive/refs/tags/v2.3.4.tar.gz && \
  tar -xf v2.3.4.tar.gz && \
  cd binwalk-2.3.4 && \
  sed -i 's/^install_ubireader//g;s/^install_sasquatch//g' deps.sh && \
  git clone --quiet --depth 1 --branch "master" https://github.com/devttys0/sasquatch && \
  cd sasquatch && \
  wget https://github.com/devttys0/sasquatch/pull/51.patch && patch -p1 <51.patch && \
  ./build.sh && cd .. && \
  echo y | ./deps.sh && \
  python3 setup.py install

COPY ./sudo /usr/bin/sudo

RUN ln -s /bin/ntfs-3g /bin/mount.ntfs-3g && \
    chmod 777 /usr/bin/sudo && \
    mkdir -p /work/FirmAE && \
    mkdir -p /work/firmwares && \
    unstuff /usr/local/bin/

ENV USER=root
ENV FIRMAE_DOCKER=true
