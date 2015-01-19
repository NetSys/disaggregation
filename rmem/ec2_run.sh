#remote_mem bw latency inject get_record


/root/spark-ec2/copy-dir .
SLAVES=`cat /root/spark-ec2/slaves`
for slave in $SLAVES; do
  echo "-------------reseting $slave -------------------"
  ssh root@$slave "/root/disaggregation/rmem/ec2_reset.sh $1 $2 $3 $4 $5"
done

/root/ephemeral-hdfs/bin/hadoop fs -rmr /wikicount
/root/spark/bin/spark-submit --class "WordCount" --master "spark://$master:7077" "/root/disaggregation/WordCount_spark/target/scala-2.10/simple-project_2.10-1.0.jar" "hdfs://$master:9000/wiki" "hdfs://$master:9000/wikicount" 2>&1 | python spark_state.py $1 $2 $3 $4 $5 -v


