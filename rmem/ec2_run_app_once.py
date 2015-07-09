# Copyright 2015 The Regents of The University California
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# Contact petergao@berkeley.edu for any question

from optparse import OptionParser
import os
import time
from ec2_utils import *
import datetime
import sys

def parse_args():
  parser = OptionParser(usage="ec2_run_exp_once.py [options]")
 
  parser.add_option("--task", help="Task to be done")
  parser.add_option("-r", "--remote-memory", type="float", default=6, help="Remote memory size in GB")
  parser.add_option("-b", "--bandwidth", type="float", default=10, help="Bandwidth in Gbps")
  parser.add_option("-l", "--latency", type="int", default=1, help="Latency in us")
  parser.add_option("-i", "--inject", action="store_true", default=False, help="Whether to inject latency")
  parser.add_option("-t", "--trace", action="store_true", default=False, help="Whether to get trace")
  parser.add_option("--diff-latency", action="store_true", default=False, help="Experiment on different latency")
  parser.add_option("--iter", type="int", default=1, help="Number of iterations")

  (opts, args) = parser.parse_args()
  return opts

def install_blktrace():
  install_if_not_exist = '''
      blktrace 2> /dev/null
      if [ $? -ne 1 ]
      then
        yum install blktrace -y
      fi
  '''
  slaves_run_bash(install_if_not_exist)

def turn_off_os_swap():
  banner("Turn off os swap")
  turn_off_swap = '''
      if [ -n "$(cat /proc/swaps | grep /mnt/swap)" ];
        then swapoff /mnt/swap;
      fi;
  '''
  slaves_run_bash(turn_off_swap)


def clean_existing_rmem():
  banner("exiting rmem")
  close_rmem = '''
    cd /root/disaggregation/rmem;
    while [ -n "$(cat /proc/swaps | grep /dev/rmem0)" ];
      do swapoff /dev/rmem0;
    done;

    while [ -n "$(lsmod | grep rmem)" ];
      do rmmod rmem;
    done;

    while [ -d "swap" ];
      do rmdir swap;
    done;

    free > /dev/null && sync && echo 3 > /proc/sys/vm/drop_caches && free > /dev/null;
  '''

  slaves_run_bash(close_rmem)

def setup_rmem(rmem_gb, bw_gbps, latency_us, inject, trace):
  banner("setting up rmem")
  remote_page = int(rmem_gb * 1024 * 1024 * 1024 / 4096)
  bandwidth_bps = int(bw_gbps * 1000 * 1000 * 1000)
  inject_int = 1 if inject else 0
  trace_int = 1 if trace else 0

  install_rmem = '''
    cd /root/disaggregation/rmem
    make;
    mkdir -p swap;
    insmod rmem.ko npages=%d;
    mkswap /dev/rmem0;
    swapon /dev/rmem0;
    echo 0 > /proc/sys/fs/rmem/read_bytes;
    echo 0 > /proc/sys/fs/rmem/write_bytes;

    echo %d > /proc/sys/fs/rmem/bandwidth_bps;
    echo %d > /proc/sys/fs/rmem/latency_ns;
    echo %d > /proc/sys/fs/rmem/inject_latency;
    echo %d > /proc/sys/fs/rmem/get_record;
    ''' % (remote_page, bandwidth_bps, latency_us, inject_int, trace_int)


  slaves_run_bash(install_rmem)

def log_trace():
  banner("log trace")
  get_disk_mem_log = '''
    cd /root/disaggregation/rmem/
    echo 0 > .app_running.tmp
    if [ -a rmem_log.txt ]
    then
      rm rmem_log.txt
    fi

    if [ -z "$(mount | grep /sys/kernel/debug)" ]
    then
      mount -t debugfs debugfs /sys/kernel/debug
    fi

    if [ -a .disk_io.blktrace.0 ]
    then
      rm .disk_io.blktrace.0
    fi

    if [ -a .disk_io.blktrace.1 ]
    then
      rm .disk_io.blktrace.1
    fi

    start_time=$(date +%s%N)
    echo ${start_time:0:${#start_time}-3} > .metadata
    blktrace -d /dev/xvda1 -o .disk_io &

    count=0
    while true; do
      cat /proc/rmem_log >> rmem_log.txt
      count=$((count+1))
      if [ $(( count % 10 )) -eq 0 ] && [ $(cat .app_running.tmp) -eq 1 ]; then
        break
      fi
    done

    killall -SIGINT blktrace
  '''
  slaves_run_bash(get_disk_mem_log, silent = True, background = True)

def collect_trace():
  banner("collect trace")
  slaves_run("echo 1 > /root/disaggregation/rmem/.app_running.tmp")
  time.sleep(0.5)
  
  result_dir = "/root/disaggregation/rmem/results/%s" % run_and_get("date +%y%m%d%H%M%S")[1]
  run("mkdir %s" % result_dir)

  count = 0
  slaves = get_slaves()
  for s in slaves:
    scp_from("/root/disaggregation/rmem/rmem_log.txt", "%s/%d-mem-%s" % (result_dir, count, s), s)
    scp_from("/root/disaggregation/rmem/.disk_io.blktrace.0", "%s/%d-disk-%s.blktrace.0" % (result_dir, count, s), s)
    scp_from("/root/disaggregation/rmem/.disk_io.blktrace.1", "%s/%d-disk-%s.blktrace.1" % (result_dir, count, s), s)
    scp_from("/root/disaggregation/rmem/.metadata", "%s/%d-meta-%s" % (result_dir, count, s), s)
    
def get_rw_bytes():
  reads = []
  writes = []
  slaves = get_slaves()
  for s in slaves:
    read_bytes = int(run_and_get("ssh root@%s \"cat /proc/sys/fs/rmem/read_bytes\"" % s)[1].replace("\n",""))
    write_bytes = int(run_and_get("ssh root@%s \"cat /proc/sys/fs/rmem/write_bytes\"" % s)[1].replace("\n",""))
    reads.append(read_bytes)
    writes.append(write_bytes)
  return (reads, writes)

def run_exp(task, rmem_gb, bw_gbps, latency_us, inject, trace):
  banner("Sync rmem code")
  run("cd /root/disaggregation/rmem; /root/spark-ec2/copy-dir .")

  banner("Prepare environment")
  slaves_run("mkdir -p /root/disaggregation/rmem/.remote_commands")
  install_blktrace()

  turn_off_os_swap()

  clean_existing_rmem()

  setup_rmem(rmem_gb, bw_gbps, latency_us, inject, trace)

  if trace:
    log_trace()

  master = get_master()

  banner("Running app")
  if task == "wordcount":
    run("/root/ephemeral-hdfs/bin/hadoop fs -rmr /wikicount")
    start_time = time.time()
    run("/root/spark/bin/spark-submit --class \"WordCount\" --master \"spark://%s:7077\" \"/root/disaggregation/apps/WordCount_spark/target/scala-2.10/simple-project_2.10-1.0.jar\" \"hdfs://%s:9000/wiki\" \"hdfs://%s:9000/wikicount\"" % (master, master, master) )
    time_used = time.time() - start_time
  elif task == "terasort":
    run("/root/ephemeral-hdfs/bin/start-mapred.sh")
    run("/root/ephemeral-hdfs/bin/hadoop dfs -rmr /sortoutput")
    start_time = time.time()
    run("/root/ephemeral-hdfs/bin/hadoop jar /root/ephemeral-hdfs/hadoop-examples-1.0.4.jar terasort hdfs://%s:9000/sortinput hdfs://%s:9000/sortoutput" % (master, master))
    time_used = time.time() - start_time
    run("/root/ephemeral-hdfs/bin/stop-mapred.sh")
  elif task == "graphlab":
    all_run("rm -rf /mnt/netflix_m/out")
    start_time = time.time()
    run("mpiexec -n 10 -hostfile /root/spark-ec2/slaves /root/disaggregation/apps/collaborative_filtering/als --matrix /mnt/netflix_m/ --max_iter=3 --ncpus=1 --minval=1 --maxval=5 --predictions=/mnt/netflix_m/out/out")
    time_used = time.time() - start_time
  elif task == "memcached":
    slaves_run("memcached -d -m 6000 -u root")
    run("cd /root/disaggregation/apps/memcached;java -cp jars/ycsb.jar:jars/spymemcached-2.7.1.jar:jars/slf4j-simple-1.6.1.jar:jars/slf4j-api-1.6.1.jar  com.yahoo.ycsb.LoadGenerator -load -P workloads/workloadb")
    start_time = time.time()
    run("cd /root/disaggregation/apps/memcached;java -cp jars/ycsb.jar:jars/spymemcached-2.7.1.jar:jars/slf4j-simple-1.6.1.jar:jars/slf4j-api-1.6.1.jar  com.yahoo.ycsb.LoadGenerator -t -P workloads/workloadb")
    time_used = time.time() - start_time
    slaves_run("killall memcached")

  if trace:
    collect_trace()

  (reads, writes) = get_rw_bytes()
  print "Remote Reads:"
  print reads
  print "Remote Writes:"
  print writes

  clean_existing_rmem()

  print "Execution time:" + str(time_used)
  return time_used

def teragen(size = 2):
  num_record = size * 1024 * 1024 * 1024 / 100
  master = get_master()
  run("/root/ephemeral-hdfs/bin/start-mapred.sh")
  run("/root/ephemeral-hdfs/bin/hadoop dfs -rmr /sortinput")
  run("/root/ephemeral-hdfs/bin/hadoop jar /root/ephemeral-hdfs/hadoop-examples-1.0.4.jar teragen %d hdfs://%s:9000/sortinput" % (num_record, master))
  run("/root/ephemeral-hdfs/bin/stop-mapred.sh")

def memcached_install():
  all_run("yum install memcached -y")
  #all_run("yum install python-memcached")

def graphlab_install():
  all_run("yum install openmpi -y")
  all_run("yum install openmpi-devel -y")
  slaves_run("echo 'export LD_LIBRARY_PATH=/usr/lib64/openmpi/lib/:$LD_LIBRARY_PATH' >> /root/.bashrc; echo 'export PATH=/usr/lib64/openmpi/bin/:$PATH' >> /root/.bashrc")
  run("echo 'export LD_LIBRARY_PATH=/usr/lib64/openmpi/lib/:$LD_LIBRARY_PATH' >> /root/.bash_profile; echo 'export PATH=/usr/lib64/openmpi/bin/:$PATH' >> /root/.bash_profile")
  run("/root/spark-ec2/copy-dir /root/disaggregation/apps/collaborative_filtering")

def graphlab_prepare():
  all_run("cd /mnt; rm netflix_mm; wget -q http://www.select.cs.cmu.edu/code/graphlab/datasets/netflix_mm; rm -rf netflix_m; mkdir netflix_m; cd netflix_m; head -n 200000000 ../netflix_mm | sed -e '1,3d' > netflix_mm; rm ../netflix_mm;", background = True)

def wordcount_prepare():
  run("mount /dev/xvdg /root/ssd")
  run("/root/ephemeral-hdfs/bin/hadoop dfsadmin -safemode leave")
  run("/root/ephemeral-hdfs/bin/hadoop fs -rm /wiki")
  run("/root/ephemeral-hdfs/bin/hadoop fs -put /root/ssd/f7168.txt /wiki")

def run_diff_latency(opts):

  confs = []
  confs.append((False, 0, 0))
  confs.append((True, 1, 100))
  confs.append((True, 1, 40))
  confs.append((True, 1, 10))
  confs.append((True, 10, 100))
  confs.append((True, 10, 40))
  confs.append((True, 10, 10))
 
  results = {}
  for conf in confs:
    results[conf] = []

  for i in range(0, opts.iter):
    for conf in confs:
      time = run_exp(opts.task, opts.remote_memory, conf[2], conf[1], conf[0], False)
      results[conf].append(time)


  log("\n\n\n")
  log("================== Started exp at:%s ==================" % str(datetime.datetime.now()))
  log('Argument %s' % str(sys.argv))

  for conf in results:
    result_str = "Latency: %d BW: %d Result: %s" % (conf[1], conf[2], ",".join(map(str, results[conf])))
    log(result_str)
    print result_str

def stop_tachyon():
  run("/root/tachyon/bin/tachyon-stop.sh")

def install_all():
  graphlab_install()

def prepare_all():
  stop_tachyon()
  teragen()
  graphlab_prepare()
  wordcount_prepare()

def main():
  opts = parse_args()
  run_exp_tasks = ["wordcount", "terasort", "graphlab", "memcached"]
  
  if opts.diff_latency:
    run_diff_latency(opts)
  elif opts.task in run_exp_tasks:
    run_exp(opts.task, opts.remote_memory, opts.bandwidth, opts.latency, opts.inject, opts.trace)
  elif opts.task == "wordcount-prepare":
    wordcount_prepare()
  elif opts.task == "terasort-prepare":
    teragen()
  elif opts.task == "graphlab-install":
    graphlab_install()
  elif opts.task == "graphlab-prepare":
    graphlab_prepare()
  elif opts.task == "memcached-install":
    memcached_install()
  elif opts.task == "prepare-all":
    prepare_all()
  elif opts.task == "install-all":
    install_all()
  else:
    print "Unknown task %s" % opts.task

if __name__ == "__main__":
  main()
