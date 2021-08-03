#!/bin/bash

docker ps -a | cut -d " " -f 1 | xargs docker rm -f
sudo losetup -D
