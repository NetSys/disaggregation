
for i in `seq 1 8`;
do
#  echo $i
  cp /root/spark/conf/spark-env.sh.$i /root/spark/conf/spark-env.sh
  /root/spark-ec2/copy-dir /root/spark/conf/
  /root/spark/sbin/stop-all.sh
  /root/spark/sbin/start-all.sh
  python execute.py --task wordcount --vary-latency -r 17.67
done;
