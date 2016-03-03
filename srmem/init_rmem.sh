#!/bin/sh

if [ -n "$(cat /proc/swaps | grep /mnt/swap)" ]
then
  swapoff /mnt/swap
fi
insmod rmem.ko npages=$1

for s in $(ls /dev/rmem*);
do
  mkswap $s
  swapon $s
done
            
