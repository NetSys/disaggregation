/root/tachyon/bin/tachyon-stop.sh
mount /dev/xvdg /root/ssd
/root/ephemeral-hdfs/bin/hadoop dfsadmin -safemode leave
/root/ephemeral-hdfs/bin/hadoop fs -rm /wiki
/root/ephemeral-hdfs/bin/hadoop fs -put /root/ssd/f7168.txt /wiki
