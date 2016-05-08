#!/bin/sh

if [ -n "$(cat /proc/swaps | grep /mnt/swap)" ]
then
  swapoff /mnt/swap
fi
insmod rmem.ko npages=$1 ndev=$2

for s in $(ls /dev/rmem*);
do
  mkswap -f $s
  swapon $s
done
            
