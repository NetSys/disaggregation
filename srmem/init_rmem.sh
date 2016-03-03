#!/bin/sh

make -s
mkdir -p swap
if [ -n "$(cat /proc/swaps | grep /mnt/swap)" ]
then
  swapoff /mnt/swap
fi
insmod rmem.ko npages=$1


            
mkswap /dev/rmem0;      
swapon /dev/rmem0;
            
