#!/bin/bash

if [ $# -ne 4 ]; then
    echo $0: Usage: ./analyses_all.sh [iid] [brand] [target address] [sql ip]
    exit 1
fi

set -e
set -u

if [ -e ./firmae.config ]; then
    source ./firmae.config
elif [ -e ../firmae.config ]; then
    source ../firmae.config
else
    echo "Error: Could not find 'firmae.config'!"
    exit 1
fi

IID=${1}
BRAND=${2}
TARGET=${3}
PSQL_IP=${4}
WORK_DIR=`get_scratch ${IID}`
LOG_DIR="${WORK_DIR}/analysis_log"
EXPLOIT_DIR="$LOG_DIR/exploits"

mkdir -p $LOG_DIR
mkdir -p $EXPLOIT_DIR

sleep 10

echo '[*] FirmAE web server initializer'
echo "${BRAND}, ${TARGET}, ${IID}"
{ time ./initializer.py $BRAND $TARGET > $LOG_DIR/initializer_log 2>&1 ; } 2> $LOG_DIR/initializer_time
#{ time nmap -O -sV $TARGET -oX $LOG_DIR/nmap_log.txt ; } 2> $LOG_DIR/nmap_time

#echo '[*] fuzzer'
#{ time ./fuzzer/fuzzer.py ci $BRAND $IID $TARGET $WORK_DIR $LOG_DIR > $LOG_DIR/fuzzer_log_ci ; } 2> $LOG_DIR/fuzzer_ci_time
#{ time ./fuzzer/fuzzer.py bof $BRAND $IID $TARGET $WORK_DIR $LOG_DIR > $LOG_DIR/fuzzer_log_bof ; } 2> $LOG_DIR/fuzzer_bof_time

# TODO: re-run web server after fuzzer.
echo '[*] rsf'
cd routersploit
timeout --preserve-status --signal SIGINT 600 ./rsf.py $TARGET > $LOG_DIR/rsf 2>&1
cd -
echo '[*] analyzer finished'
echo true > ${LOG_DIR}/result
