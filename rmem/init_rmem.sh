#!/bin/sh

make
mkdir -p swap
sudo insmod rmem.ko npages=$1
sudo mkswap /dev/rmem0
sudo swapon /dev/rmem0
echo 0 | sudo tee /proc/sys/fs/rmem/read_bytes
echo 0 | sudo tee /proc/sys/fs/rmem/write_bytes
