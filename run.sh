#!/bin/bash

function print_usage()
{
    echo "Usage: ${0} [mode]... [brand] [firmware|firmware_directory]"
    echo "mode: use one option at once"
    echo "      -r, --run     : run mode         - run emulation (no quit)"
    echo "      -c, --check   : check mode       - check network reachable and web access (quit)"
    echo "      -a, --analyze : analyze mode     - analyze vulnerability (quit)"
    echo "      -d, --debug   : debug mode       - debugging emulation (no quit)"
    echo "      -b, --boot    : boot debug mode  - kernel boot debugging using QEMU (no quit)"
}

if [ $# -ne 3 ]; then
    print_usage ${0}
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

function get_option()
{
    OPTION=${1}
    if [ ${OPTION} = "-c" ] || [ ${OPTION} = "--check" ]; then
        echo "check"
    elif [ ${OPTION} = "-a" ] || [ ${OPTION} = "--analyze" ]; then
        echo "analyze"
    elif [ ${OPTION} = "-r" ] || [ ${OPTION} = "--run" ]; then
        echo "run"
    elif [ ${OPTION} = "-d" ] || [ ${OPTION} = "--debug" ]; then
        echo "debug"
    elif [ ${OPTION} = "-b" ] || [ ${OPTION} = "--boot" ]; then
        echo "boot"
    else
        echo "none"
    fi
}

function get_brand()
{
  INFILE=${1}
  BRAND=${2}
  if [ ${BRAND} = "auto" ]; then
    echo `./scripts/util.py get_brand ${INFILE} ${PSQL_IP}`
  else
    echo ${2}
  fi
}

OPTION=`get_option ${1}`
if [ ${OPTION} == "none" ]; then
  print_usage ${0}
  exit 1
fi

if (! id | egrep -sqi "root"); then
  echo -e "[\033[31m-\033[0m] This script must run with 'root' privilege"
  exit 1
fi

BRAND=${2}
WORK_DIR=""
IID=-1

function run_emulation()
{
    echo "[*] ${1} emulation start!!!"
    INFILE=${1}
    BRAND=`get_brand ${INFILE} ${BRAND}`
    FILENAME=`basename ${INFILE%.*}`
    PING_RESULT=false
    WEB_RESULT=false
    IP=''

    if [ "${BRAND}" = "auto" ]; then
      echo -e "[\033[31m-\033[0m] Invalid brand ${INFILE}"
      return
    fi

    if [ -n "${FIRMAE_DOCKER-}" ]; then
      if ( ! ./scripts/util.py check_connection _ $PSQL_IP ); then
        echo -e "[\033[31m-\033[0m] docker container failed to connect to the hosts' postgresql!"
        return
      fi
    fi

    # Omit the argument '-b' when $BRAND is empty.
    [ -n "$BRAND" ] && brand_arg="-b $BRAND" || brand_arg=""

    # ================================
    # extract filesystem from firmware
    # ================================
    t_start="$(date -u +%s.%N)"

    # If the brand is not specified in the argument, it will be inferred 
    # automatically from the path of the image file.
    timeout --preserve-status --signal SIGINT 300 \
        ./sources/extractor/extractor.py $brand_arg -sql $PSQL_IP -np \
        -nk $INFILE images 2>&1 >/dev/null

    IID=`./scripts/util.py get_iid $INFILE $PSQL_IP`
    if [ ! "${IID}" ]; then
        echo -e "[\033[31m-\033[0m] extractor.py failed!"
        return
    fi

    # ================================
    # extract kernel from firmware
    # ================================
    # If the brand is not specified in the argument, it will be inferred 
    # automatically from the path of the image file.
    timeout --preserve-status --signal SIGINT 300 \
        ./sources/extractor/extractor.py $brand_arg -sql $PSQL_IP -np \
        -nf $INFILE images 2>&1 >/dev/null

    WORK_DIR=`get_scratch ${IID}`
    mkdir -p ${WORK_DIR}
    chmod a+rwx "${WORK_DIR}"
    chown -R "${USER}" "${WORK_DIR}"
    chgrp -R "${USER}" "${WORK_DIR}"
    echo $FILENAME > ${WORK_DIR}/name
    echo $BRAND > ${WORK_DIR}/brand
    sync

    if [ ${OPTION} = "check" ] && [ -e ${WORK_DIR}/result ]; then
        if (egrep -sqi "true" ${WORK_DIR}/result); then
            RESULT=`cat ${WORK_DIR}/result`
            return
        fi
        rm ${WORK_DIR}/result
    fi

    if [ ! -e ./images/$IID.tar.gz ]; then
        echo -e "[\033[31m-\033[0m] Extracting root filesystem failed!"
        echo "extraction fail" > ${WORK_DIR}/result
        return
    fi

    echo "[*] extract done!!!"
    t_end="$(date -u +%s.%N)"
    time_extract="$(bc <<<"$t_end-$t_start")"
    echo $time_extract > ${WORK_DIR}/time_extract

    # ================================
    # check architecture
    # ================================
    t_start="$(date -u +%s.%N)"
    ARCH=`./scripts/getArch.py ./images/$IID.tar.gz $PSQL_IP`
    echo "${ARCH}" > "${WORK_DIR}/architecture"

    if [ -e ./images/${IID}.kernel ]; then
      ./scripts/inferKernel.py ${IID}
    fi

    if [ ! "${ARCH}" ]; then
        echo -e "[\033[31m-\033[0m] Get architecture failed!"
        echo "get architecture fail" > ${WORK_DIR}/result
        return
    fi
    if ( check_arch ${ARCH} == 0 ); then
        echo -e "[\033[31m-\033[0m] Unknown architecture! - ${ARCH}"
        echo "not valid architecture : ${ARCH}" > ${WORK_DIR}/result
        return
    fi

    echo "[*] get architecture done!!!"
    t_end="$(date -u +%s.%N)"
    time_arch="$(bc <<<"$t_end-$t_start")"
    echo $time_arch > ${WORK_DIR}/time_arch

    if (! egrep -sqi "true" ${WORK_DIR}/web); then
        # ================================
        # make qemu image
        # ================================
        t_start="$(date -u +%s.%N)"
        ./scripts/tar2db.py -i $IID -f ./images/$IID.tar.gz -h $PSQL_IP \
            2>&1 > ${WORK_DIR}/tar2db.log
        t_end="$(date -u +%s.%N)"
        time_tar="$(bc <<<"$t_end-$t_start")"
        echo $time_tar > ${WORK_DIR}/time_tar

        t_start="$(date -u +%s.%N)"
        ./scripts/makeImage.sh $IID $ARCH $FILENAME \
            2>&1 > ${WORK_DIR}/makeImage.log
        t_end="$(date -u +%s.%N)"
        time_image="$(bc <<<"$t_end-$t_start")"
        echo $time_image > ${WORK_DIR}/time_image

        # ================================
        # infer network interface
        # ================================
        t_start="$(date -u +%s.%N)"
        echo "[*] infer network start!!!"
        # TIMEOUT is set in "firmae.config". This TIMEOUT is used for initial
        # log collection.
        TIMEOUT=$TIMEOUT FIRMAE_NET=${FIRMAE_NET} \
          ./scripts/makeNetwork.py -i $IID -q -o -a ${ARCH} \
          &> ${WORK_DIR}/makeNetwork.log
        ln -s ./run.sh ${WORK_DIR}/run_debug.sh | true
        ln -s ./run.sh ${WORK_DIR}/run_analyze.sh | true
        ln -s ./run.sh ${WORK_DIR}/run_boot.sh | true

        t_end="$(date -u +%s.%N)"
        time_network="$(bc <<<"$t_end-$t_start")"
        echo $time_network > ${WORK_DIR}/time_network
    else
        echo "[*] ${INFILE} already succeed emulation!!!"
    fi

    if (egrep -sqi "true" ${WORK_DIR}/ping); then
        PING_RESULT=true
        IP=`cat ${WORK_DIR}/ip`
    fi
    if (egrep -sqi "true" ${WORK_DIR}/web); then
        WEB_RESULT=true
    fi

    echo -e "\n[IID] ${IID}\n[\033[33mMODE\033[0m] ${OPTION}"
    if ($PING_RESULT); then
        echo -e "[\033[32m+\033[0m] Network reachable on ${IP}!"
    fi
    if ($WEB_RESULT); then
        echo -e "[\033[32m+\033[0m] Web service on ${IP}"
        echo true > ${WORK_DIR}/result
    else
        echo false > ${WORK_DIR}/result
    fi

    if [ ${OPTION} = "analyze" ]; then
        # ================================
        # analyze firmware (check vulnerability)
        # ================================
        t_start="$(date -u +%s.%N)"
        if ($WEB_RESULT); then
            echo "[*] Waiting web service..."
            ${WORK_DIR}/run_analyze.sh &
            IP=`cat ${WORK_DIR}/ip`
            check_network ${IP} false

            echo -e "[\033[32m+\033[0m] start pentest!"
            cd analyses
            ./analyses_all.sh $IID $BRAND $IP $PSQL_IP
            cd -

            sync
            kill $(ps aux | grep `get_qemu ${ARCH}` | awk '{print $2}') 2> /dev/null
            sleep 2
        else
            echo -e "[\033[31m-\033[0m] Web unreachable"
        fi
        t_end="$(date -u +%s.%N)"
        time_analyze="$(bc <<<"$t_end-$t_start")"
        echo $time_analyze > ${WORK_DIR}/time_analyze

    elif [ ${OPTION} = "debug" ]; then
        # ================================
        # run debug mode.
        # ================================
        if ($PING_RESULT); then
            echo -e "[\033[32m+\033[0m] Run debug!"
            IP=`cat ${WORK_DIR}/ip`
            ./scratch/$IID/run_debug.sh &
            check_network ${IP} true

            sleep 10
            ./debug.py ${IID}

            sync
            kill $(ps aux | grep `get_qemu ${ARCH}` | awk '{print $2}') 2> /dev/null | true
            sleep 2
        else
            echo -e "[\033[31m-\033[0m] Network unreachable"
        fi
    elif [ ${OPTION} = "run" ]; then
        # ================================
        # just run mode
        # ================================
        check_network ${IP} false &
        ${WORK_DIR}/run.sh
    elif [ ${OPTION} = "boot" ]; then
        # ================================
        # boot debug mode
        # ================================
        BOOT_KERNEL_PATH=`get_boot_kernel ${ARCH} true`
        BOOT_KERNEL=./binaries/`basename ${BOOT_KERNEL_PATH}`
        echo -e "[\033[32m+\033[0m] Connect with gdb-multiarch -q ${BOOT_KERNEL} -ex='target remote:1234'"
        ${WORK_DIR}/run_boot.sh
    fi

    echo "[*] cleanup"
    echo "======================================"

}

FIRMWARE=${3}

if [ ${OPTION} = "debug" ] && [ -d ${FIRMWARE} ]; then
    echo -e "[\033[31m-\033[0m] select firmware file on debug mode!"
    exit 1
fi

if [ ! -d ${FIRMWARE} ]; then
    run_emulation ${FIRMWARE}
else
    FIRMWARES=`find ${3} -type f`

    for FIRMWARE in ${FIRMWARES}; do
        if [ ! -d "${FIRMWARE}" ]; then
            run_emulation ${FIRMWARE}
        fi
    done
fi
