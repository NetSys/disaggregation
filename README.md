#Disaggregation Emulator#
This is an emulator for evaluating current application performance in disaggregated datacenter. The current code can run on EC2 without any modification. So you need an EC2 account to run the experiment. But there is no fundamental limitation that prevents you from using your own cluster. 

The RDMA-based swap device is available at https://github.com/pxgao/rdma_swap_dev

Memory access trace is available on s3 https://github.com/NetSys/disaggregation/blob/master/download-trace.sh

##Quick Start##
On your local computer, go to ec2 folder

```
cd disaggregation/ec2
```
create an ec2 cluster with 5 worker nodes

with VPC (You need to setup VPC first)
```
./spark-ec2 -k AWS_KEY_ID -i AWS_KEY_FILE -s 5 --region us-east-1 --zone us-east-1a --vpc-id VPC-ID --subnet-id SUBNET-ID --instance-type m3.2xlarge --ami ami-ee9d14f9 launch ddc-exp
```
without VPC
```
./spark-ec2 -k AWS_KEY_ID -i AWS_KEY_FILE -s 5 --region us-east-1 --zone us-east-1a --instance-type m3.2xlarge --spot-price 0.4 --no-ganglia --copy-aws-credentials --ami ami-ee9d14f9 launch ddc-exp
```
once the cluster is craeted, login
```
./spark-ec2 -k AWS_KEY_ID -i AWS_KEY_FILE login ddc-exp
```
Now you have a 5-node EC2 cluster, go to /root/disaggregation/rmem
```
cd /root/disaggregation/rmem
```
Everytime a new cluster is created, we need to first prepare the environment for the experiments.
```
python execute.py --task prepare-env
```
You may need to press "Y" when formatting the HDFS

To run a experiment, you need to prepare the data. I will demonstrate how to run terasort here.
First, you need to prepare the data by running
```
python execute.py --task terasort-prepare
```
This will load the input data to HDFS.
To run experiment,
```
python execute.py --task terasort --vary-both-latency-bw --iter 10
```
This will run terasort with different bandwith (10Gbps - 100Gbps) and latency(1us - 40us) combinations for 10 times. (This will take a long time. You may want to reduce that to 1 times for initial test
To run other experiment such as "fix latency at 5us and vary bandwidth", "fix bandwidth at 40g and vary latency", "vary percentage of local memory", and "application degradation in a network" run
```
python execute.py --task terasort --vary-latency --iter 10
python execute.py --task terasort --vary-bw --iter 10
python execute.py --task terasort --vary-remote-mem --iter 10
python execute.py --task terasort --slowdown-cdf-exp 100g --iter 10
```
You can run other application by replacing "terasort" with "wordcount" (Spark Wordcount), "wordcount-hadoop" (Hadoop Wordcount), "terasort-spark" (Spark Terasort), "graphlab", "memcached", "bdb" (Spark SQL), "memcached", "timely" (Timely Dataflow).

##Folders##

**apps** The applications to run on ddc emulator

**ec2** scripts to launch ec2 clusters

**result** result plots

**rmem**	ddc emulator

**srmem**	ddc emulator with partitioned memory space

**turbo-sub** pHost simulator




