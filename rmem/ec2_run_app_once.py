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
import xml.etree.ElementTree as etree
from xml.dom import minidom
import threading

def parse_args():
  parser = OptionParser(usage="ec2_run_exp_once.py [options]")
 
  parser.add_option("--task", help="Task to be done")
  parser.add_option("-r", "--remote-memory", type="float", default=22.09, help="Remote memory size in GB")
  parser.add_option("-b", "--bandwidth", type="float", default=10, help="Bandwidth in Gbps")
  parser.add_option("-l", "--latency", type="int", default=1, help="Latency in us")
  parser.add_option("-i", "--inject", action="store_true", default=False, help="Whether to inject latency")
  parser.add_option("-t", "--trace", action="store_true", default=False, help="Whether to get trace")
  parser.add_option("--vary-latency", action="store_true", default=False, help="Experiment on different latency")
  parser.add_option("--vary-latency-40g", action="store_true", default=False, help="Experiment on different latency with 40G bandwidth")
  parser.add_option("--iter", type="int", default=1, help="Number of iterations")
  parser.add_option("--teragen-size", type="float", default=50.0, help="Sort input data size (GB)")

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
  latency_ns = latency_us * 1000
  inject_int = 1 if inject else 0
  trace_int = 1 if trace else 0


  install_rmem = '''
    cd /root/disaggregation/rmem

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
    ''' % (remote_page, bandwidth_bps, latency_ns, inject_int, trace_int)


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
  run("mkdir -p %s" % result_dir)

  count = 0
  slaves = get_slaves()
  for s in slaves:
    scp_from("/root/disaggregation/rmem/rmem_log.txt", "%s/%d-mem-%s" % (result_dir, count, s), s)
    scp_from("/root/disaggregation/rmem/.disk_io.blktrace.0", "%s/%d-disk-%s.blktrace.0" % (result_dir, count, s), s)
    scp_from("/root/disaggregation/rmem/.disk_io.blktrace.1", "%s/%d-disk-%s.blktrace.1" % (result_dir, count, s), s)
    scp_from("/root/disaggregation/rmem/.metadata", "%s/%d-meta-%s" % (result_dir, count, s), s)
    count += 1
    
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

def sync_rmem_code():
  banner("Sync rmem code")
  run("cd /root/disaggregation/rmem; /root/spark-ec2/copy-dir .")
  slaves_run("cd /root/disaggregation/rmem; make")

def update_hadoop_conf():
  def get_conf(k, v):
    elem = etree.Element("property")
    name = etree.Element("name")
    value = etree.Element("value")
    name.text = k
    value.text = v
    elem.insert(0, name)
    elem.insert(1, value)
    return elem


  tree=etree.parse("/root/ephemeral-hdfs/conf/mapred-site.xml")
  root=tree.getroot()
  if "io.sort.mb" in etree.tostring(root):
    print "conf file is already updated"
    return
  map = get_conf("mapreduce.admin.map.child.java.opts", "-Xmx26000m")
  reduce = get_conf("mapreduce.admin.reduce.child.java.opts", "-Xmx26000m")
  slowstart = get_conf("mapred.reduce.slowstart.completed.maps", "1.0")
  iosort = get_conf("io.sort.mb", "2047")

  root.append(map)
  root.append(reduce)
  root.append(slowstart)
  root.append(iosort)

  tree.write("/root/ephemeral-hdfs/conf/mapred-site.xml")

memcached_kill_loadgen_on=False
def memcached_kill_loadgen(deadline):
  global memcached_kill_loadgen_on
  memcached_kill_loadgen_on = True
  while time.time() < deadline:
    time.sleep(30)
    if memcached_kill_loadgen_on == False:
      print ">>>>>>>>>>>>>>>>>>>>memcached_kill_loadgen == False, return<<<<<<<<<<<<<<<<"
      return
  print ">>>>>>>>>>>>>>>>>>>>>Timeout, kill process loadgen<<<<<<<<<<<<<<<<<<<"
  slaves_run("pid=\$(jps | grep LoadGenerator | cut -d ' ' -f 1);kill \$pid")
  memcached_kill_loadgen_on=False

memmon_peak_remaining_ram = 100000
memmon_on = False

def mem_monitor_worker():
  global memmon_peak_remaining_ram
  global memmon_on
  memmon_peak_remaining_ram = 100000
  memmon_on = True
  while memmon_on:
    remaining = get_cluster_remaining_memory()
    if remaining < memmon_peak_remaining_ram:
      memmon_peak_remaining_ram = remaining
    time.sleep(5)

def mem_monitor_start():
  assert(memmon_on == False)
  thrd = threading.Thread(target=mem_monitor_worker)
  thrd.start()

def mem_monitor_stop():
  global memmon_peak_remaining_ram
  global memmon_on
  memmon_on = False
  return memmon_peak_remaining_ram

def get_memcached_avg_latency():
  r = run_and_get("cat /root/disaggregation/apps/memcached/results.txt | grep AverageLatency")[1]
  return float(r.replace("[GET] AverageLatency, ","").replace("us",""))

def slaves_get_memcached_avg_latency():
  total = 0
  slaves = get_slaves()
  for s in slaves:
    r = run_and_get("ssh %s \"cat /root/disaggregation/apps/memcached/results.txt | grep AverageLatency\"" % s)[1]
    total += float(r.replace("[GET] AverageLatency, ","").replace("us",""))
  return total / len(slaves)


class ExpResult:
  runtime = 0.0
  min_ram_gb = -1.0
  memcached_latency_us = -1.0
  task = ""
  def get(self):
    if self.task == "memcached":
      return str(self.runtime) + ":" + str(self.memcached_latency_us)
    else:
      return self.runtime


def run_exp(task, rmem_gb, bw_gbps, latency_us, inject, trace, profile = False):
  global memcached_kill_loadgen_on
  result = ExpResult()
  result.task = task

  min_ram = 0

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
    if profile:
      mem_monitor_start()
    run("/root/ephemeral-hdfs/bin/hadoop jar /root/disaggregation/apps/hadoop_terasort/hadoop-examples-1.0.4.jar terasort -Dmapred.map.tasks=20 -Dmapred.reduce.tasks=10 -Dmapreduce.map.java.opts=-Xmx25000 -Dmapreduce.reduce.java.opts=-Xmx25000 -Dmapreduce.map.memory.mb=26000 -Dmapreduce.reduce.memory.mb=26000 -Dmapred.reduce.slowstart.completed.maps=1.0 /sortinput /sortoutput")
    if profile:
      min_ram = mem_monitor_stop()
      result.min_ram_gb = min_ram
    time_used = time.time() - start_time
    run("/root/ephemeral-hdfs/bin/stop-mapred.sh")
    run("/root/ephemeral-hdfs/bin/hadoop dfs -rmr /mnt")
    run("/root/ephemeral-hdfs/bin/hadoop dfs -rmr /sortoutput")
    slaves_run("rm -rf /mnt/ephemeral-hdfs/taskTracker/root/jobcache/*; rm -rf /mnt2/ephemeral-hdfs/taskTracker/root/jobcache/*; rm -rf /mnt99/taskTracker/root/jobcache/*; rm -rf /mnt/ephemeral-hdfs/mapred/local/taskTracker/root/jobcache/*; rm -rf /mnt2/ephemeral-hdfs/mapred/local/taskTracker/root/jobcache/*;  rm -rf /mnt99/mapred/local/taskTracker/root/jobcache/*")

  elif task == "graphlab":
    all_run("rm -rf /mnt2/netflix_m/out")
    start_time = time.time()
    run("mpiexec -n 5 -hostfile /root/spark-ec2/slaves /root/disaggregation/apps/collaborative_filtering/als --matrix /mnt2/netflix_m/ --max_iter=3 --ncpus=6 --minval=1 --maxval=5 --predictions=/mnt2/netflix_m/out/out")
    time_used = time.time() - start_time

  elif task == "memcached":
    slaves_run("memcached -d -m 26000 -u root")
    run("/root/spark-ec2/copy-dir /root/disaggregation/apps/memcached/jars; /root/spark-ec2/copy-dir /root/disaggregation/apps/memcached/workloads")
    thrd = threading.Thread(target=memcached_kill_loadgen, args=(time.time() + 10 * 60,))
    thrd.start()
    slaves_run_parallel("cd /root/disaggregation/apps/memcached;java -cp jars/ycsb_local.jar:jars/spymemcached-2.7.1.jar:jars/slf4j-simple-1.6.1.jar:jars/slf4j-api-1.6.1.jar  com.yahoo.ycsb.LoadGenerator -load -P workloads/workloadb_ins")
    memcached_kill_loadgen_on = False
    thrd.join()
    all_run("rm /root/disaggregation/apps/memcached/results.txt")
    start_time = time.time()
    slaves_run_parallel("cd /root/disaggregation/apps/memcached;java -cp jars/ycsb_local.jar:jars/spymemcached-2.7.1.jar:jars/slf4j-simple-1.6.1.jar:jars/slf4j-api-1.6.1.jar  com.yahoo.ycsb.LoadGenerator -t -P workloads/workloadb")
    result.memcached_latency_us = slaves_get_memcached_avg_latency()
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

  print "Execution time:" + str(time_used) + " Min Ram:" + str(min_ram)
  result.runtime = time_used
  return result

def teragen(size):
  num_record = size * 1024 * 1024 * 1024 / 100
  master = get_master()
  run("/root/ephemeral-hdfs/bin/start-mapred.sh")
  run("/root/ephemeral-hdfs/bin/hadoop dfs -rmr /sortinput")
  run("/root/ephemeral-hdfs/bin/hadoop jar /root/disaggregation/apps/hadoop_terasort/hadoop-examples-1.0.4.jar teragen %d hdfs://%s:9000/sortinput" % (num_record, master))
  run("/root/ephemeral-hdfs/bin/stop-mapred.sh")

def terasort_prepare_and_run(opts, size, bw_gb, latency_us, inject):
  run("/root/ephemeral-hdfs/bin/hadoop dfs -rmr /mnt")
  run("/root/ephemeral-hdfs/bin/hadoop dfs -rmr /sortinput")
  run("/root/ephemeral-hdfs/bin/hadoop dfs -rmr /sortoutput")
  teragen(opts.teragen_size)
  return run_exp("terasort", opts.remote_memory, bw_gb, latency_us, inject, False, profile = True)

def terasort_vary_size(opts):
  sizes = [180, 150, 120, 90, 60, 30]

  confs = [] #(inject, latency, bw, size)
  for s in sizes:
    confs.append((False, 0, 0, s))
    confs.append((True, 10, 40, s))


  results = {}

  for conf in confs:
    results[conf] = []

  for i in range(0, opts.iter):
    for conf in confs:
      print "Running iter %d conf %s" % (i, str(conf))
      res = terasort_prepare_and_run(opts, conf[3], conf[2], conf[1], conf[0] )
      results[conf].append(res)

  log("\n\n\n")
  log("================== Started exp at:%s ==================" % str(datetime.datetime.now()))
  log('Argument %s' % str(sys.argv))

  for conf in results:
    result_str = "Latency: %d BW: %d Size: %f Result: %s" % (conf[1], conf[2], conf[3], ",".join(map(lambda r: str(r.get()), results[conf])))
    log(result_str)
    print result_str

  print "--------------------"

  for conf in results:
    result_str = "Latency: %d BW: %d Size: %f RemainingRam: %s" % (conf[1], conf[2], conf[3], ",".join(map(lambda r: str(r.min_ram_gb), results[conf])))
    log(result_str) 
    print result_str


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
  cmd = '''
    cd /mnt2; 
    rm netflix_mm; 
    wget -q http://www.select.cs.cmu.edu/code/graphlab/datasets/netflix_mm; 
    rm -rf netflix_m; 
    mkdir netflix_m; 
    cd netflix_m; 
    for i in `seq 1 6`; 
    do 
      head -n 100000000 ../netflix_mm | sed -e '1,3d' >> netflix_mm; 
    done ; 
    rm ../netflix_mm;
  '''
  slaves_run_bash(cmd, silent=True, background = True)
  run(cmd)

def wordcount_prepare():
  run("mkdir -p /root/ssd; mount /dev/xvdg /root/ssd")
  run("/root/ephemeral-hdfs/bin/hadoop dfsadmin -safemode leave")
  run("/root/ephemeral-hdfs/bin/hadoop fs -rm /wiki")
  run("/root/ephemeral-hdfs/bin/hadoop fs -put /root/ssd/wiki /wiki")

def execute(opts):

  confs = []
  if opts.vary_latency:
    confs.append((False, 0, 0))
    confs.append((True, 1, 100))
    confs.append((True, 1, 40))
    confs.append((True, 1, 10))
    confs.append((True, 5, 100))
    confs.append((True, 5, 40))
    confs.append((True, 5, 10))
    confs.append((True, 10, 100))
    confs.append((True, 10, 40))
    confs.append((True, 10, 10))
  elif opts.vary_latency_40g:
    latency_40g = [1, 5, 10, 20, 40, 60, 80, 100]
    for l in latency_40g:
      confs.append((True, l, 40))
  else:
    confs.append((opts.inject, opts.latency, opts.bandwidth))
 
  results = {}
  for conf in confs:
    results[conf] = []

  for i in range(0, opts.iter):
    for conf in confs:
      print "Running iter %d, conf %s" % (i, str(conf))
      time = run_exp(opts.task, opts.remote_memory, conf[2], conf[1], conf[0], opts.trace).get()
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
  run("/root/ephemeral-hdfs/bin/hadoop dfs -rmr /tachyon")

def update_kernel():
  all_run("yum install kernel-devel -y; yum install kernel -y", background=True)

def install_mosh():
  run("sudo yum --enablerepo=epel install -y mosh")

def install_all():
  update_kernel()
  slaves_run("mkdir -p /root/disaggregation/rmem/.remote_commands")
  install_blktrace()
  graphlab_install()
  memcached_install()
  install_mosh()

def prepare_env():
  stop_tachyon()
  turn_off_os_swap()
  sync_rmem_code()
  update_hadoop_conf()

def prepare_all(opts):
  prepare_env()
  teragen(opts.teragen_size)
  graphlab_prepare()
  wordcount_prepare()


def main():
  opts = parse_args()
  run_exp_tasks = ["wordcount", "terasort", "graphlab", "memcached"]
  
  
  if opts.task in run_exp_tasks:
    execute(opts)
  elif opts.task == "terasort-vary-size":
    terasort_vary_size(opts)
  elif opts.task == "wordcount-prepare":
    wordcount_prepare()
  elif opts.task == "terasort-prepare":
    teragen(opts.teragen_size)
  elif opts.task == "graphlab-install":
    graphlab_install()
  elif opts.task == "graphlab-prepare":
    graphlab_prepare()
  elif opts.task == "memcached-install":
    memcached_install()
  elif opts.task == "prepare-env":
    prepare_env()
  elif opts.task == "prepare-all":
    prepare_all(opts)
  elif opts.task == "install-all":
    install_all()
  elif opts.task == "test":
    get_cluster_remaining_memory()
  else:
    print "Unknown task %s" % opts.task

if __name__ == "__main__":
  main()
