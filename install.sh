#!/bin/bash
# exit when any command fails
set -e
set -o pipefail
# see https://intoli.com/blog/exit-on-errors-in-bash-scripts/ for usage
# keep track of the last executed command
trap 'last_command=$current_command; current_command=$BASH_COMMAND' DEBUG
# echo an error message before exiting
trap 'echo "\"${last_command}\" command filed with exit code $?."' EXIT

abort()
{
    echo >&2 '
***************
*** ABORTED ***
***************
'
    echo "An error occurred. Please report to creator n0s3y. Exiting..." >&2
    exit 1
}

trap 'abort' 0



sudo apt-get update || exit
sudo apt-get install -y curl wget tar git ruby python3 python3-pip bc || exit 
sudo python3 -m pip install --upgrade pip
sudo python3 -m pip install coloredlogs


# for docker
sudo apt-get install -y docker.io 

# postgresql
sudo apt-get install -y postgresql
sudo /etc/init.d/postgresql restart
sudo -u postgres bash -c "psql -c \"CREATE USER firmadyne WITH PASSWORD 'firmadyne';\"" || true
sudo -u postgres createdb -O firmadyne firmware || true
sudo -u postgres psql -d firmware < ./database/schema || true
echo "listen_addresses = '172.17.0.1,127.0.0.1,localhost'" | sudo -u postgres tee --append /etc/postgresql/*/main/postgresql.conf
echo "host all all 172.17.0.1/24 trust" | sudo -u postgres tee --append /etc/postgresql/*/main/pg_hba.conf

sudo apt install -y libpq-dev
python3 -m pip install psycopg2 psycopg2-binary

sudo apt-get install -y busybox-static bash-static fakeroot dmsetup kpartx netcat-openbsd nmap python3-psycopg2 snmp uml-utilities util-linux vlan

# for binwalk
wget https://github.com/ReFirmLabs/binwalk/archive/refs/tags/v2.3.3.tar.gz && \
  tar -xf v2.3.3.tar.gz && \
  cd binwalk-2.3.3 && \
  echo y | ./deps.sh && \
  sudo python3 setup.py install
sudo apt-get install -y mtd-utils gzip bzip2 tar arj lhasa p7zip p7zip-full cabextract fusecram cramfsswap squashfs-tools sleuthkit default-jdk cpio lzop lzma srecord zlib1g-dev liblzma-dev liblzo2-dev unzip

cd - # back to root of project

python3 -m pip install python-lzo cstruct ubi_reader
sudo apt-get install -y python3-magic openjdk-8-jdk unrar

# for analyzer, initializer
sudo apt-get install -y python3-bs4
python3 -m pip install selenium
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo dpkg -i google-chrome-stable_current_amd64.deb; sudo apt-get -fy install
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
# If an error occurs, the abort() function will be called.
#----------------------------------------------------------
# Done!
trap : 0

echo >&2 '
************
*** DONE *** 
************
'
