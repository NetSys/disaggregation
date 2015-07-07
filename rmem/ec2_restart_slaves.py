import os

os.system("cat /root/disaggregation/rmem/.slave_list > /root/ephemeral-hdfs/conf/slaves")
os.system("cat /root/disaggregation/rmem/.slave_list > /root/spark/conf/slaves")
os.system("cat /root/disaggregation/rmem/.slave_list > /root/spark-ec2/slaves")

#os.system("/root/spark-ec2/copy-dir /root/")

os.system("/root/spark/sbin/stop-all.sh")
os.system("/root/spark/sbin/start-all.sh")


os.system("/root/ephemeral-hdfs/bin/stop-dfs.sh")
os.system("/root/ephemeral-hdfs/bin/start-dfs.sh")

