SLAVES=`cat /root/spark-ec2/slaves`

for slave in $SLAVES; do
  echo "installing blktrace on $slave"
  ssh root@$slave "yum install blktrace -y"
done

