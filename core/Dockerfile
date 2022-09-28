FROM ubuntu:18.04
MAINTAINER Mingeun Kim <pr0v3rbs@kaist.ac.kr>, Minkyo Seo <0xsaika@gmail.com>

RUN apt-get update && apt-get -y dist-upgrade
RUN apt-get install -y apt-utils
RUN apt-get install -y wget bc psmisc ruby telnet
RUN apt-get install -y net-tools iputils-ping iptables iproute2 curl
RUN apt-get install -yy python3 python3-pip
RUN python3 -m pip install --upgrade pip

RUN apt-get install -y libpq-dev
RUN python3 -m pip install psycopg2 psycopg2-binary

RUN apt-get install -y busybox-static bash-static fakeroot git kpartx netcat-openbsd nmap python3-psycopg2 snmp uml-utilities util-linux vlan

# for binwalk
# bypass tzdata interaction
ENV DEBIAN_FRONTEND=noninteractive
RUN curl -Ls https://api.github.com/repos/ReFirmLabs/binwalk/releases/latest | \
    grep -wo "\"https.*tarball.*\"" | sed 's/"//g' | wget -qi - -O binwalk.tar.gz && \
    tar -xf binwalk.tar.gz && \
    cd ReFirmLabs-binwalk-*/ && \
    python3 setup.py install
RUN apt-get install -y mtd-utils gzip bzip2 tar arj lhasa p7zip p7zip-full cabextract fusecram cramfsswap squashfs-tools sleuthkit default-jdk cpio lzop lzma srecord zlib1g-dev liblzma-dev liblzo2-dev

RUN python3 -m pip install python-lzo cstruct git+https://github.com/sviehb/jefferson ubi_reader
RUN apt-get install -y python3-magic unrar

RUN apt-get install -y openjdk-8-jdk
RUN python3 -m pip install git+https://github.com/ReFirmLabs/binwalk

# for qemu
RUN apt-get install -y qemu-system-arm qemu-system-mips qemu-system-x86 qemu-utils
# for rust dependency
RUN apt-get install rustc cargo -y
RUN python3 -m pip install setuptools_rust
# for analyzer
RUN python3 -m pip install selenium bs4 requests future paramiko pysnmp==4.4.6 pycryptodome
# google chrome
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add -
RUN echo 'deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main' | tee /etc/apt/sources.list.d/google-chrome.list
RUN apt-get update
RUN apt-get install -y google-chrome-stable
RUN apt-get install -y ntfs-3g
RUN ln -s /bin/ntfs-3g /bin/mount.ntfs-3g

COPY ./sudo /usr/bin/sudo
RUN chmod 777 /usr/bin/sudo

RUN mkdir -p /work/FirmAE
RUN mkdir -p /work/firmwares
COPY sasquatch /usr/local/bin/
COPY cramfsck /usr/local/bin/
COPY yaffshiv /usr/local/bin/
COPY unstuff /usr/local/bin/

ENV USER=root
ENV FIRMAE_DOCKER=true
