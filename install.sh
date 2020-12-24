#!/bin/bash

sudo apt-get update
sudo apt-get install -y curl wget git ruby python3 python3-pip
python3 -m pip install coloredlogs

# for docker
sudo apt-get install -y docker.io

# postgresql
sudo apt-get install -y postgresql
sudo /etc/init.d/postgresql restart
sudo -u postgres bash -c "psql -c \"CREATE USER firmadyne WITH PASSWORD 'firmadyne';\""
sudo -u postgres createdb -O firmadyne firmware
sudo -u postgres psql -d firmware < ./database/schema
echo "listen_addresses = '172.17.0.1,127.0.0.1,localhost'" | sudo -u postgres tee --append /etc/postgresql/*/main/postgresql.conf
echo "host all all 172.17.0.1/24 trust" | sudo -u postgres tee --append /etc/postgresql/*/main/pg_hba.conf

sudo apt install libpq-dev
python3 -m pip install psycopg2 psycopg2-binary

sudo apt-get install -y busybox-static bash-static fakeroot dmsetup kpartx netcat-openbsd nmap python3-psycopg2 snmp uml-utilities util-linux vlan

# for binwalk
sudo apt-get install -y binwalk mtd-utils gzip bzip2 tar arj lhasa p7zip p7zip-full cabextract fusecram cramfsswap squashfs-tools sleuthkit default-jdk cpio lzop lzma srecord zlib1g-dev liblzma-dev liblzo2-dev unzip

git clone https://github.com/devttys0/sasquatch && (cd sasquatch && ./build.sh && cd -)
git clone https://github.com/devttys0/yaffshiv && (cd yaffshiv && sudo python3 setup.py install)
cp core/unstuff /usr/local/bin/

python3 -m pip install python-lzo cstruct git+https://github.com/sviehb/jefferson ubi_reader
sudo apt-get install -y python3-magic openjdk-8-jdk unrar

# for analyzer, initializer
sudo apt-get install -y python3-bs4
python3 -m pip install selenium
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo dpkg -i google-chrome-stable_current_amd64.deb; apt-get -fy install
rm google-chrome-stable_current_amd64.deb
python3 -m pip install -r ./analyses/routersploit/requirements.txt
cd ./analyses/routersploit && patch -p1 < ../routersploit_patch && cd -

# for qemu
sudo apt-get install -y qemu-system-arm qemu-system-mips qemu-system-x86 qemu-utils

if ! test -e "./analyses/chromedriver"; then
    wget https://chromedriver.storage.googleapis.com/2.38/chromedriver_linux64.zip
    unzip chromedriver_linux64.zip -d ./analyses/
    rm -rf chromedriver_linux64.zip
fi
