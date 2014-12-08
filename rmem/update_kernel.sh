SLAVES=`cat /root/spark-ec2/slaves`

for slave in $SLAVES; do
  echo "updating $slave"
  ssh root@$slave "yum install kernel-devel-3.14.25-23.45.amzn1.x86_64 -y"
  ssh root@$slave "yum install kernel-3.14.25-23.45.amzn1.x86_64 -y"
  ssh root@$slave "reboot"
done

