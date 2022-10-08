#!/bin/bash

FILE=$(zenity --file-selection --title="Select a firmware file" --file-filter="*.bin")
if [ -z  "$FILE" ]
then
    exit 1
fi

BRAND=$(zenity --entry --entry-text="Type the brand of the firmware" --text="Tell me...")

if zenity --question --title="FirmAE firmware runner" --text="Would you like to open this file with the FirmAE Debugger?"
then
    sudo ./run.sh -d $ "file://${FILE}"
else
    zenity --text-info --filename="$FILE" --title="Firmware runner"
fi