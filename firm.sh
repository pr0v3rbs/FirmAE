#!/bin/bash
# exit when any command fails
set -e
set -o pipefail
# see https://intoli.com/blog/exit-on-errors-in-bash-scripts/ for usage
# keep track of the last executed command
trap 'last_command=$current_command; current_command=$BASH_COMMAND' DEBUG
# echo an error message before exiting
trap 'echo "\"${last_command}\" command filed with exit code $?."' EXIT

abort()
{
    echo >&2 '
***************
*** ABORTED ***
***************
'
    echo "An error occurred. Exiting..." >&2
    exit 1
}

trap 'abort' 0




#CODE
#
#
#
#
if zenity --question --title="Confirm Installation" --text="Are you sure you to install in this directory?" --no-wrap 
    then
        echo "Starting..."
    else 
        exit
fi

sudo apt update
# If this fails, script should break/exit

# Download git
sudo apt install git

# Clone FirmAE & install it
x-terminal-emulator -e ./download.sh 
x-terminal-emulator -e ./install.sh 
#
#
#
# End of CODE


# If an error occurs, the abort() function will be called.
#----------------------------------------------------------
# Done!
trap : 0

echo >&2 '
************
*** DONE, FirmAE installed without error codes to be worried about.  *** 
************
'

# Continuity by starting the emulation script
if zenity --question --title="Start emulation" --text="Do you want to start the emulation?" --no-wrap 
    then
        ./runner.sh
    else 
        exit
fi
