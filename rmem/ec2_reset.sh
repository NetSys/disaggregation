#reset.sh <remote_mem> <bw> <latency>
cd /root/disaggregation/rmem
./exit_rmem.sh
./exit_rmem.sh
free > /dev/null && sync && echo 3 > /proc/sys/vm/drop_caches && free > /dev/null
./init_rmem.sh $1
echo $2 > /proc/sys/fs/rmem/bandwidth_bps
echo $3 > /proc/sys/fs/rmem/latency_ns
echo 1 > /proc/sys/fs/rmem/inject_latency
echo 0 > /proc/sys/fs/rmem/get_record
