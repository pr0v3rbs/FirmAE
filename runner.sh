#!/bin/bash



FILE=$(zenity --file-selection --title="Select a firmware file" --file-filter="*.bin")
if [ -z  "$FILE" ]
then
    exit 1
fi
BRAND=$(zenity --entry --title="Add brand" --text="Enter name of brand:")
if zenity --question --title="FirmAE firmware runner" --text="Would you like to start the emulation?"

MODE=$(zenity --entry --title="Add mode. Choose between: '-d', '-c', '-a'. See the oficial documentation for more." --text="Enter mode:")


then
    ./init.sh
    sudo ./run.sh ${MODE} ${BRAND} ${FILE}
else
    zenity --text-info --filename="$FILE" --title="Firmware runner"
fi
