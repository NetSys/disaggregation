#!/bin/sh
#init_rmem.sh remote_page(GB) inject(0or1) bw(Gbps) latency(us)

make

sudo insmod rmem.ko npages=$(echo "($1*1024*1024/4/1)" | bc)
sudo mkswap /dev/rmem0
sudo swapon /dev/rmem0
echo 0 > /proc/sys/fs/rmem/read_bytes
echo 0 > /proc/sys/fs/rmem/write_bytes

echo $2 > /proc/sys/fs/rmem/inject_latency
echo $(($3*1000*1000*1000)) > /proc/sys/fs/rmem/bandwidth_bps
echo $(($4*1000)) > /proc/sys/fs/rmem/latency_ns
