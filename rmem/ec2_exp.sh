cd /root/disaggregation/rmem

bws=( 100000000000 40000000000 10000000000 )
las=( 1000 10000 )

get_record=0

remote_mem=1400111
master=$(cat /root/spark-ec2/masters)

echo ============= >> ec2_exp_log.txt



for aaa in {1..10}
do
  ./ec2_run.sh $remote_mem 0 0 0 $get_record
  for latency in "${las[@]}"
  do
    for bw in "${bws[@]}"
    do
      ./ec2_run.sh $remote_mem $bw $latency 1 $get_record
    done
  done
done
