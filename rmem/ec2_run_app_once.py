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

def parse_args():
  parser = OptionParser(usage="ec2_run_exp_once.py [options]")
 
  parser.add_option("--task", help="Task to be done")
  parser.add_option("-r", "--remote-memory", type="float", default=6, help="Remote memory size in GB")
  parser.add_option("-b", "--bandwidth", type="float", default=10, help="Bandwidth in Gbps")
  parser.add_option("-l", "--latency", type="int", default=1, help="Latency in us")
  parser.add_option("-i", "--inject", action="store_true", default=False, help="Whether to inject latency")
  parser.add_option("-t", "--trace", action="store_true", default=False, help="Whether to get trace")

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
    


def run_spark_exp(task, rmem_gb, bw_gbps, latency_us, inject, trace):
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

  if task == "wordcount":
    run("/root/ephemeral-hdfs/bin/hadoop fs -rmr /wikicount")
    start_time = time.time()
    run("/root/spark/bin/spark-submit --class \"WordCount\" --master \"spark://%s:7077\" \"/root/disaggregation/WordCount_spark/target/scala-2.10/simple-project_2.10-1.0.jar\" \"hdfs://%s:9000/wiki\" \"hdfs://%s:9000/wikicount\"" % (master, master, master) )
    time_used = time.time() - start_time
  elif task == "sort":
    pass

  if trace:
    collect_trace()

  clean_existing_rmem()

  print "Execution time:" + str(time_used)
  return time_used

def teragen(size = 1):
  num_record = size * 1024 * 1024 * 1024 / 100
  master = get_master()
  run("/root/ephemeral-hdfs/bin/start-mapred.sh")
  run("/root/ephemeral-hdfs/bin/hadoop dfs -rmr /sortinput")
  run("/root/ephemeral-hdfs/bin/hadoop jar /root/ephemeral-hdfs/hadoop-examples-1.0.4.jar teragen %d hdfs://%s:9000/sortinput" % (num_record, master))
  run("/root/ephemeral-hdfs/bin/stop-mapred.sh")

def main():
  opts = parse_args()
  if opts.task == "wordcount":
    run_spark_exp(opts.task, opts.remote_memory, opts.bandwidth, opts.latency, opts.inject, opts.trace)
  elif opts.task == "teragen":
    teragen()
  elif opts.task == "sort":
    run_spark_exp(opts.task, opts.remote_memory, opts.bandwidth, opts.latency, opts.inject, opts.trace)
  else:
    print "Unknow task %s" % opts.task

if __name__ == "__main__":
  main()
