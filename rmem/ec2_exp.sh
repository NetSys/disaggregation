/root/spark-ec2/copy-dir .

SLAVES=`cat /root/spark-ec2/slaves`

for slave in $SLAVES; do
  echo "reseting $slave"
  ssh root@$slave "/root/disaggregation/rmem/ec2_reset.sh"
done

#/root/ephemeral-hdfs/bin/hadoop fs -rmr /data/wiki_counts
