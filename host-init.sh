# Tested on MacOS under `brew install postgresql@14`
createdb -U firmadyne
psql -c "CREATE USER firmadyne WITH PASSWORD 'firmadyne';"
createdb -O firmadyne firmware
psql -d firmware < ./database/schema
CONFIG_LOCATION=$(psql -c 'SHOW config_file;' -t -A)
HBA_LOCATION=$(psql -c 'SHOW hba_file;' -t -A)
echo "$CONFIG_LOCATION, $HBA_LOCATION"
echo "listen_addresses = '172.17.0.1,127.0.0.1,localhost'" | tee -a $CONFIG_LOCATION
echo "host all all 172.17.0.1/24 trust" | tee -a $HBA_LOCATION

echo "[*] Completed initializing database for docker to connect to"