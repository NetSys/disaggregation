#reset.sh <remote_mem> <bw> <latency> <inject> <get_record>

if [ -n "$(cat /proc/swaps | grep /mnt/swap)" ]
then
  swapoff /mnt/swap
fi

cd /root/disaggregation/rmem

./ec2_exit_rmem.sh
free > /dev/null && sync && echo 3 > /proc/sys/vm/drop_caches && free > /dev/null
./ec2_init_rmem.sh $1
echo $2 > /proc/sys/fs/rmem/bandwidth_bps
echo $3 > /proc/sys/fs/rmem/latency_ns
echo $4 > /proc/sys/fs/rmem/inject_latency
echo $5 > /proc/sys/fs/rmem/get_record

