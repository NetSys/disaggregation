cd /root/disaggregation/rmem

bws=( 100000000000 40000000000 10000000000 )
las=( 1000 10000 )

remote_mem=1400111
master=$(cat /root/spark-ec2/masters)

echo ============= >> ec2_exp_log.txt

#remote_mem bw latency inject
run()
{
  /root/spark-ec2/copy-dir .
  SLAVES=`cat /root/spark-ec2/slaves`
  for slave in $SLAVES; do
    echo "-------------reseting $slave -------------------"
    ssh root@$slave "/root/disaggregation/rmem/ec2_reset.sh $1 $2 $3 $4"
  done

  /root/ephemeral-hdfs/bin/hadoop fs -rmr /wikicount
  /root/spark/bin/spark-submit --class "WordCount" --master "spark://$master:7077" "/root/disaggregation/WordCount_spark/target/scala-2.10/simple-project_2.10-1.0.jar" "hdfs://$master:9000/wiki" "hdfs://$master:9000/wikicount" 2>&1 | python spark_state.py $1 $2 $3 $4 -v 

}


for aaa in {1..10}
do
  run $remote_mem 0 0 0
  for latency in "${las[@]}"
  do
    for bw in "${bws[@]}"
    do
      run $remote_mem $bw $latency 1
    done
  done
done
