#init_rmem.sh remote_page(GB) inject(0or1) bw(Gbps) latency(us)
ITER=1
res=()

echo "./execute_local.sh $@"

cd /root/disaggregation/rmem
./init_rmem.sh $1 $2 $3 $4

for i in `seq 0 $(($ITER-1))`
do
	free > /dev/null && sync && echo 3 > /proc/sys/vm/drop_caches && free > /dev/null
	a=$(cd /root/stream-scaling/; export OMP_NUM_THREADS=16; ./stream | tail -n 4 | grep Triad: | awk '{print $2}')	
	echo $@ $a
	res[$i]=$a
done

free > /dev/null && sync && echo 3 > /proc/sys/vm/drop_caches && free > /dev/null
cd /root/disaggregation/rmem
./exit_rmem.sh

echo $@ ${res[*]} >> run_rmem.sh.log
