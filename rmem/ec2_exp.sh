remote_mem=1500000
bw=40000000000
latency=10

/root/spark-ec2/copy-dir .

SLAVES=`cat /root/spark-ec2/slaves`

for slave in $SLAVES; do
  echo "-------------reseting $slave -------------------"
  ssh root@$slave "/root/disaggregation/rmem/ec2_reset.sh $remote_mem $bw $latency"
done

#/root/ephemeral-hdfs/bin/hadoop fs -rmr /data/wiki_counts
