#!/bin/bash

if [ $# -ne 4 ]; then
    echo $0: Usage: ./analyses_all.sh [iid] [brand] [target address] [sql ip]
    exit 1
fi

set -e
set -u

IID=${1}
BRAND=${2}
TARGET=${3}
PSQL_IP=${4}
LOG_DIR="analyses_log/$BRAND/$IID"
EXPLOIT_DIR="$LOG_DIR/exploits"

mkdir -p analyses_log
mkdir -p $LOG_DIR
mkdir -p $EXPLOIT_DIR

sleep 10

echo '[*] FirmAE web server initializer'
{ time ./initializer.py $BRAND $TARGET > $LOG_DIR/initializer_log ; } 2> $LOG_DIR/initializer_time
{ time nmap -O -sV $TARGET -oX $LOG_DIR/nmap_log.txt ; } 2> $LOG_DIR/nmap_time
echo '[*] fuzzer'
{ time ./fuzzer/fuzzer.py ci $BRAND $IID $TARGET > $LOG_DIR/fuzzer_log_ci ; } 2> $LOG_DIR/fuzzer_ci_time
{ time ./fuzzer/fuzzer.py bof $BRAND $IID $TARGET > $LOG_DIR/fuzzer_log_bof ; } 2> $LOG_DIR/fuzzer_bof_time
echo '[*] rsf'
cd routersploit && timeout --preserve-status --signal SIGINT 300 ./rsf.py $TARGET > ../$LOG_DIR/rsf && cd -
echo '[*] analyzer finished'
echo true > ${LOG_DIR}/result
