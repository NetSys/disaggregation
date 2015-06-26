SLAVES=`cat /root/spark-ec2/slaves`

for slave in $SLAVES; do
  echo "updating $slave"
  ssh root@$slave "yum install kernel-devel -y"
  ssh root@$slave "yum install kernel -y"
  ssh root@$slave "reboot"
done

