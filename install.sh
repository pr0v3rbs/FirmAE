#!/bin/bash

sudo apt-get update
sudo apt-get install -y curl wget tar git ruby python2 python3 python3-pip bc python3-coloredlogs python3-pip python3-psycopg2 python3-lzo python3-magic openjdk-17-jdk unrar docker.io postgresql libpq-dev busybox-static bash-static fakeroot dmsetup kpartx netcat-openbsd nmap python3-psycopg2 snmp uml-utilities util-linux vlan mtd-utils gzip bzip2 tar arj lhasa p7zip p7zip-full cabextract cramfsswap squashfs-tools sleuthkit default-jdk cpio lzop lzma srecord zlib1g-dev liblzma-dev liblzo2-dev unzip python3-bs4 python3-selenium qemu-system-arm qemu-system-mips qemu-system-x86 qemu-utils

python3 -m pip install cstruct ubi_reader


# postgresql
sudo /etc/init.d/postgresql restart
sudo -u postgres bash -c "psql -c \"CREATE USER firmadyne WITH PASSWORD 'firmadyne';\""
sudo -u postgres createdb -O firmadyne firmware
sudo -u postgres psql -d firmware < ./database/schema
echo "listen_addresses = '172.17.0.1,127.0.0.1,localhost'" | sudo -u postgres tee --append /etc/postgresql/*/main/postgresql.conf
echo "host all all 172.17.0.1/24 trust" | sudo -u postgres tee --append /etc/postgresql/*/main/pg_hba.conf

# python3 -m pip install psycopg2 psycopg2-binary


# for binwalk
wget https://github.com/ReFirmLabs/binwalk/archive/refs/tags/v2.3.3.tar.gz && \
  tar -xf v2.3.3.tar.gz && \
  cd binwalk-2.3.3 && \
  sed -i 's/^install_unstuff//g' deps.sh && \
  echo y | ./deps.sh && \
  sudo python3 setup.py install
sudo apt-get install -y 

cd - # back to root of project

sudo cp core/unstuff /usr/local/bin/


# for analyzer, initializer
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo dpkg -i google-chrome-stable_current_amd64.deb; sudo apt-get -fy install
rm google-chrome-stable_current_amd64.deb
python3 -m pip install -r ./analyses/routersploit/requirements.txt
cd ./analyses/routersploit && patch -p1 < ../routersploit_patch && cd -

if ! test -e "./analyses/chromedriver"; then
    wget https://chromedriver.storage.googleapis.com/2.38/chromedriver_linux64.zip
    unzip chromedriver_linux64.zip -d ./analyses/
    rm -rf chromedriver_linux64.zip
fi
