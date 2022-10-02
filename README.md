# FirmAE

Stable release hosted by Mick Beer, aka n0s3y, to provide a release that is up to date with the current KALI release BUT with maintained code to make sure you can emulate the firmware you want to.

poc:
![image](https://user-images.githubusercontent.com/105726899/191462312-e8393e3e-8c3c-45f3-8aed-518f12609df1.png)

# Installation

Note that we tested FirmAE on Kali 2022.03 at 9/21/2022.

1. Clone `FirmAE`
```console
git clone --recursive https://github.com/n0s3y/FirmAE.git
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
2. Check emulation
```console
sudo ./run.sh -c <brand> <firmware>
```

After `run.sh -c` finished.

3. User-level basic debugging utility. (Useful when an emulated firmware is network reachable)

```console
sudo ./run.sh -d <brand> <firmware>
```

## OPTIONAL: Kernel-level boot debugging.

```console
sudo ./run.sh -b <brand> <firmware>
```

### Turn on/off arbitration

Check the five arbitrations environment variable in the `firmae.config`
```sh
head firmae.config
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
sudo ./docker-init.sh
```

### Parallel mode

Then, run one of the below commands. ```-ec``` checks only the emulation, and ```-ea``` checks the emulation and analyzes vulnerabilities.
```console
sudo ./docker-helper.py -ec <brand> <firmware>
sudo ./docker-helper.py -ea <brand> <firmware>
```

### Debug mode

After a firmware image successfully emulated.
```console
sudo ./docker-helper.py -ed <firmware>
```

# Evaluation

## Emulation result

Google spreadsheet -
[view](https://docs.google.com/spreadsheets/d/1dbKxr_WOZ7UmneOogug1Zykj1erpfk-GzRNni8DjroI/edit?usp=sharing)

## Dataset

Google drive -
[download](https://drive.google.com/file/d/1hdm75NVKBvs-eVH9rKb5xfgryNSnsg_8/view?usp=sharing)

```
