# FirmAE

FirmAE is a fully-automated framework that performs emulation and vulnerability analysis. FirmAE significantly increases the emulation success rate (From [Firmadyne](https://github.com/firmadyne/firmadyne)'s 16.28% to 79.36%) with five arbitration techniques. We tested FirmAE on 1,124 wireless-router and IP-camera firmware images from top eight vendors.

We also developed a dynamic analysis tool for 0-day discovery, which infers web service information based on the filesystem and kernel logs of target firmware.
By running our tool on the succesfully emulation firmware images, we discovered 12 new 0-days which affect 23 devices.

# Installation

Note that we tested FirmAE on Kali 2022.03 at 9/21/2022.

1. Clone `FirmAE`
```console
git clone --recursive https://github.com/pr0v3rbs/FirmAE
```

2. Run `download.sh` script.
```console
./download.sh
```

3. Run `install.sh` script.
```console
./install.sh
```

# Usage

1. Execute `init.sh` script.
```console
./init.sh
```

2. Prepare a firmware.
```console
$ wget ftp://ftp.dlink.eu/Products/dir/dir-868l/driver_software/DIR-868L_fw_revB_2-05b02_eu_multi_20161117.zip
```

3. Check emulation
```console
$ sudo ./run.sh -c <brand> <firmware>
```

After `run.sh -c` finished.

4. User-level basic debugging utility. (Useful when an emulated firmware is network reachable)

```console
sudo ./run.sh -d <brand> <firmware>
```

2. Kernel-level boot debugging.

```console
$ sudo ./run.sh -b <brand> <firmware>
```

## Turn on/off arbitration

Check the five arbitrations environment variable in the `firmae.config`
```sh
$ head firmae.config
#!/bin/sh

FIRMAE_BOOT=true
FIRMAE_NETWORK=true
FIRMAE_NVRAM=true
FIRMAE_KERNEL=true
FIRMAE_ETC=true

if (${FIRMAE_ETC}); then
  TIMEOUT=240
```

## Docker

First, prepare a docker image.
```console
$ sudo ./docker-init.sh
```

### Parallel mode

Then, run one of the below commands. ```-ec``` checks only the emulation, and ```-ea``` checks the emulation and analyzes vulnerabilities.
```console
$ sudo ./docker-helper.py -ec <brand> <firmware>
$ sudo ./docker-helper.py -ea <brand> <firmware>
```

### Debug mode

After a firmware image successfully emulated.
```console
$ sudo ./docker-helper.py -ed <firmware>
```

# Evaluation

## Emulation result

Google spreadsheet -
[view](https://docs.google.com/spreadsheets/d/1dbKxr_WOZ7UmneOogug1Zykj1erpfk-GzRNni8DjroI/edit?usp=sharing)

## Dataset

Google drive -
[download](https://drive.google.com/file/d/1hdm75NVKBvs-eVH9rKb5xfgryNSnsg_8/view?usp=sharing)

```
