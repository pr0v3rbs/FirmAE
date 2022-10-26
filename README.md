# FirmAE - User friendly and Error catching
This version of FirmAE has automated installation, GUI firmware debugging and error catching. 
For dev; see ./firm.sh, runner.sh for the script chain.


## The installation is done by first RECURSIVELY cloning this repo. After that you cd into the directory and run the 'firm.sh' script which will do all the work for you. When this script is done (after about 3-6 minutes), you will be greeted by a pop-up to start running a test emulation. In the type field type: 'dlink' and select the file in the FirmAE folder called: "DIR895LA1_FW113b03.bin". 




Standard official Repo information:
_____________________________________________________________________________________________________________
FirmAE is a fully-automated framework that performs emulation and vulnerability analysis. FirmAE significantly increases the emulation success rate (From [Firmadyne](https://github.com/firmadyne/firmadyne)'s 16.28% to 79.36%) with five arbitration techniques. We tested FirmAE on 1,124 wireless-router and IP-camera firmware images from top eight vendors.

### Installation

Note that we tested FirmAE on Kali 2022.3.

1. Clone `FirmAE`.
```console
git clone --recursive https://github.com/n0s3y/FirmAE
```

2. Run 'cd FirmAE'
```console
cd FirmAE
```

4. Run `firm.sh` script to install FirmAE after cloning. 
```console
./firm.sh
```
5. Run `runner.sh` script to run and debug your firmware. 
```console
./runner.sh
```
A popup to select the .bin firmware file in the FirmAE folder will popup and a type window will ask you to type in the brandname, use 'dlink' for the first test with the provided test firmware.
