#!/bin/sh

make
mkdir -p swap
insmod rmem.ko npages=$1
mkswap /dev/rmem0
swapon /dev/rmem0
echo 0 | tee /proc/sys/fs/rmem/read_bytes
echo 0 | tee /proc/sys/fs/rmem/write_bytes
