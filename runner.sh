#!/bin/bash

FILE=$(zenity --file-selection --title="Select a firmware file" --file-filter="*.bin")
if [ -z  "$FILE" ]
then
    exit 1
fi

if zenity --question --title="FirmAE firmware runner" --text="Would you like to open this file with the FirmAE Debugger?"
then
    ./init.sh
    sudo ./run.sh -d ${FILE}
else
    zenity --text-info --filename="$FILE" --title="Firmware runner"
fi
