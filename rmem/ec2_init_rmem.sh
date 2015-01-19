#!/bin/sh

make -s
mkdir -p swap
if [ -n "$(cat /proc/swaps | grep /mnt/swap)" ]
then
  swapoff /mnt/swap
fi
insmod rmem.ko npages=$1
mkswap /dev/rmem0
swapon /dev/rmem0
echo 0 > /proc/sys/fs/rmem/read_bytes
echo 0 > /proc/sys/fs/rmem/write_bytes
