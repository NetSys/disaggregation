#remote_mem bw latency inject get_record


/root/spark-ec2/copy-dir .
SLAVES=$(cat /root/spark-ec2/slaves)
master=$(cat /root/spark-ec2/masters)
for slave in $SLAVES; do
  echo "-------------reseting $slave -------------------"
  ssh root@$slave "/root/disaggregation/rmem/ec2_reset.sh $1 $2 $3 $4 $5"
done

if [ $5 -eq 1 ]
then
  for slave in $SLAVES; do
    echo "-------------setting up log at $slave -------------------"
    ssh root@$slave "/root/disaggregation/rmem/ec2_get_log.sh > /dev/null 2>&1 &"
  done
fi

/root/ephemeral-hdfs/bin/hadoop fs -rmr /wikicount
/root/spark/bin/spark-submit --class "WordCount" --master "spark://$master:7077" "/root/disaggregation/WordCount_spark/target/scala-2.10/simple-project_2.10-1.0.jar" "hdfs://$master:9000/wiki" "hdfs://$master:9000/wikicount" 2>&1 | python spark_state.py $1 $2 $3 $4 $5 -v


if [ $5 -eq 1 ]
then
  result_dir="results/$(date +%y%m%d%H%M%S)"
  mkdir $result_dir
  count=0
  for slave in $SLAVES; do
    echo "-------------retriving log at $slave -------------------"
    ssh root@$slave "echo 1 > /root/disaggregation/rmem/.app_running.tmp"
    sleep 0.5
    scp root@$slave:/root/disaggregation/rmem/rmem_log.txt $result_dir/$count-mem-$slave
    scp root@$slave:/root/disaggregation/rmem/.disk_io.blktrace.0 $result_dir/$count-disk-$slave.blktrace.0
    scp root@$slave:/root/disaggregation/rmem/.disk_io.blktrace.1 $result_dir/$count-disk-$slave.blktrace.1
    scp root@$slave:/root/disaggregation/rmem/.metadata $result_dir/$count-meta-$slave
    count=$((count+1))
  done
  echo "results in $result_dir"
fi
