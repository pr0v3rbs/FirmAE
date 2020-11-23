#!/bin/bash
set -e
set -x

# Start database
sudo service postgresql restart
echo "Waiting for DB to start..."
sleep 5
