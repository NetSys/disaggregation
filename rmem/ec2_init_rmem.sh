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
            
echo 0 > /proc/sys/fs/rmem/read_bytes;
echo 0 > /proc/sys/fs/rmem/write_bytes;
            
echo 10000000000 > /proc/sys/fs/rmem/bandwidth_bps;
echo 1000 > /proc/sys/fs/rmem/latency_ns;
echo 1 > /proc/sys/fs/rmem/inject_latency;
echo 1 > /proc/sys/fs/rmem/get_record;

#echo "4096 500000" > /proc/rmem_cdf
#echo "8192 1000000" > /proc/rmem_cdf
#cat /proc/rmem_cdf
