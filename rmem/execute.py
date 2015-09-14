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
from memcached_workload import *
def parse_args():
  parser = OptionParser(usage="execute.py [options]")
 
  parser.add_option("--task", help="Task to be done")
  parser.add_option("-r", "--remote-memory", type="float", default=22.09, help="Remote memory size in GB")
  parser.add_option("-b", "--bandwidth", type="float", default=40, help="Bandwidth in Gbps")
  parser.add_option("-l", "--latency", type="int", default=5, help="Latency in us")
  parser.add_option("-i", "--inject", action="store_true", default=False, help="Whether to inject latency")
  parser.add_option("--cdf", type="string", default="", help="Inject latency with slowdown")
  parser.add_option("-t", "--trace", action="store_true", default=False, help="Whether to get trace")
  parser.add_option("--vary-latency", action="store_true", default=False, help="Experiment on different latency")
  parser.add_option("--vary-e2e-latency", action="store_true", default=False, help="Experiment on different end to end latency")
  parser.add_option("--vary-latency-40g", action="store_true", default=False, help="Experiment on different latency with 40G bandwidth")
  parser.add_option("--vary-bw-5us", action="store_true", default=False, help="Experiment on different bw with 5us latency")
  parser.add_option("--vary-remote-mem", action="store_true", default=False, help="Experiment that varies percentage of remote memory")
  parser.add_option("--slowdown-cdf-exp", action="store_true", default=False, help="Variable latency injected with given CDF file")
  parser.add_option("--disk-vary-size", action="store_true", default=False, help="Use disk as swap, vary input size")
  parser.add_option("--iter", type="int", default=1, help="Number of iterations")
  parser.add_option("--teragen-size", type="float", default=150.0, help="Sort input data size (GB)")

  (opts, args) = parser.parse_args()
  return opts

def get_id_name_addr():
  def get_internal(name):
    return "ip-%s.ec2.internal" % run_and_get("host %s" % name)[1].split(" ")[3].replace(".", "-")

  master = get_master()
  slaves = get_slaves()

  result = [["-1", master, get_internal(master)]]
  for i in range(0, len(slaves)):
    result.append([str(i), slaves[i], get_internal(slaves[i])])

  return "\n".join([ " ".join(l) for l in result])


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
        then swapoff /mnt/swap; rm /mnt/swap;
      fi;
  '''
  slaves_run_bash(turn_off_swap)


def clean_existing_rmem(bw_gbps):
  banner("exiting rmem")
  if bw_gbps < 0:
    close_rmem = '''
      while [ -n "$(mount | grep /root/disaggregation/rmem/tmpfs)" ];
        do umount /root/disaggregation/rmem/tmpfs;
      done;
      rmdir /root/disaggregation/rmem/tmpfs;

      cd /root/disaggregation/rmem;
      while [ -n "$(cat /proc/swaps | grep /mnt2/swapdisk/swap)" ];
        do swapoff /mnt2/swapdisk/swap;
      done;
      rm /mnt2/swapdisk/swap;
    '''
  else:
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

def setup_rmem(rmem_gb, bw_gbps, latency_us, e2e_latency_us, inject, trace, slowdown_cdf, task):
  banner("setting up rmem")
  remote_page = int(rmem_gb * 1024 * 1024 * 1024 / 4096)
  bandwidth_bps = int(bw_gbps * 1000 * 1000 * 1000)
  latency_ns = latency_us * 1000
  e2e_latency_ns = e2e_latency_us * 1000
  inject_int = 1 if inject or slowdown_cdf != "" else 0
  trace_int = 1 if trace else 0

  if bw_gbps < 0:
    rmem_mb = int(rmem_gb * 1024)
    install_rmem = '''
      cd /root/disaggregation/rmem
      mkdir -p tmpfs
      mount -t tmpfs -o size=%dm tmpfs ./tmpfs/
      fallocate -l %dm ./tmpfs/a.img

      mkdir -p /mnt2/swapdisk
      swapoff /mnt2/swapdisk/swap
      rm /mnt2/swapdisk/swap
      fallocate -l %dM /mnt2/swapdisk/swap
      chmod 0600 /mnt2/swapdisk/swap
      mkswap /mnt2/swapdisk/swap
      swapon /mnt2/swapdisk/swap
    ''' % (rmem_mb, rmem_mb, rmem_mb)
    slaves_run_bash(install_rmem)
  else:
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
      echo %d > /proc/sys/fs/rmem/end_to_end_latency_ns;
      echo %d > /proc/sys/fs/rmem/inject_latency;
      echo %d > /proc/sys/fs/rmem/get_record;
      ''' % (remote_page, bandwidth_bps, latency_ns, e2e_latency_ns, inject_int, trace_int)
    slaves_run_bash(install_rmem)

    if slowdown_cdf != "":
      run("/root/spark-ec2/copy-dir /root/disaggregation/rmem/slowdown_dist")
      cdf_file = "/root/disaggregation/rmem/slowdown_dist/cdf_slowdowns_pfabric_%s.cdf" % slowdown_cdf
      slaves_run("while read -r line; do echo \$line > /proc/rmem_cdf; done < %s; diff /proc/rmem_cdf %s" % (cdf_file, cdf_file))      

def log_trace():
  banner("log trace")
  get_disk_mem_log = '''
    rm -rf /mnt2/rmem_log
    mkdir -p /mnt2/rmem_log
    cd /mnt2/rmem_log
    echo 0 > .app_running.tmp

    if [ -z "$(mount | grep /sys/kernel/debug)" ]
    then
      mount -t debugfs debugfs /sys/kernel/debug
    fi

    start_time=$(date +%s%N)
    echo ${start_time:0:${#start_time}-3} > .metadata
    blktrace -a issue -d /dev/xvda1 /dev/xvdb /dev/xvdc -D . &

    tcpdump -i eth0 2>&1 | python /root/disaggregation/rmem/tcpdump2flow.py > .nic &

    count=0
    while true; do
      cat /proc/rmem_log >> rmem_log.txt
      count=$((count+1))
      if [ $(( count % 10 )) -eq 0 ] && [ $(cat .app_running.tmp) -eq 1 ]; then
        break
      fi
    done
 
    killall -SIGINT tcpdump
    killall -SIGINT blktrace
  '''
  slaves_run_bash(get_disk_mem_log, silent = True, background = True)

def collect_trace(task):
  banner("collect trace")
  slaves_run("echo 1 > /mnt2/rmem_log/.app_running.tmp")
  time.sleep(3)
  
  result_dir = "/mnt2/results/%s_%s" % (task, run_and_get("date +%y%m%d%H%M%S")[1])
  run("mkdir -p %s" % result_dir)

  with open("%s/addr_mapping.txt" % result_dir, "w") as f:
    f.write("%s\n" % get_id_name_addr())
  slaves_run_parallel("for i in $(seq 0 7); do cat /mnt2/rmem_log/*.blktrace.$i > /mnt2/rmem_log/.disk_io.blktrace.$i; done; ")
  count = 0
  slaves = get_slaves()
  for s in slaves:
    scp_from("/mnt2/rmem_log/rmem_log.txt", "%s/%d-mem-%s" % (result_dir, count, s), s)
    for i in range(0,8):
      scp_from("/mnt2/rmem_log/.disk_io.blktrace.%d" % i, "%s/%d-disk-%s.blktrace.%d" % (result_dir, count, s, i), s)
    scp_from("/mnt2/rmem_log/.nic", "%s/%d-nic-%s" % (result_dir, count, s), s)
    scp_from("/mnt2/rmem_log/.metadata", "%s/%d-meta-%s" % (result_dir, count, s), s)
    count += 1

  return result_dir
    
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

def mkfs_xvdc_ext4():
  all_run("umount /mnt2;mkfs.ext4 /dev/xvdc;mount /dev/xvdc /mnt2")
  

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
      print "======memcached_kill_loadgen == False, return======"
      return
  print "=======Timeout, kill process loadgen======"
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
    v = r.replace("[GET] AverageLatency, ","")
    if "us" in v:
      total += float(v.replace("us",""))
    elif "ms" in v:
      total += float(v.replace("ms","")) * 1000
  return total / len(slaves)

def get_storm_trace():
  slaves = get_slaves()
  for s in slaves:
    size = run_and_get("ssh %s \"ls -la /mnt2/storm/log/metrics.log | awk '{ print \$5}'\"" % s)[1]
    if(int(size) > 0):
      run("rm -rf /mnt2/metrics.log")
      scp_from("/mnt2/storm/log/metrics.log", "/mnt2/metrics.log", s)
  slaves_run("rm -rf /mnt2/storm/log/*")

def get_storm_perf():
  if os.path.isfile("/mnt2/metrics.log"):
    f = open("/mnt2/metrics.log", "r")
    split_sum = 0.0
    split_count = 0
    count_sum = 0.0
    count_count = 0
    record_sum = {}
    record_count = {}
    for line in f:
      arr = line.strip().split("\t")
      if len(arr) < 5:
        continue
      entity = arr[2].strip()
      key = arr[3].strip()
      value = arr[4].strip()
      bolt = entity.split(":")[1]
      #get latency
      if key == "__execute-latency" and (bolt == "split" or bolt == "count") and "default=" in value:
        latency = float(value.replace("}","").replace("{","").split(":")[1].replace("default=",""))
        if bolt == "split":
          split_sum += latency
          split_count += 1
        else:
          count_sum += latency
          count_count += 1
      #get throughput
      if key == "execute_count":
        if entity not in record_sum:
          record_sum[entity] = 0
          record_count[entity] = 0
        record_sum[entity] += int(value)
        record_count[entity] += 1
    print split_sum, split_count, count_sum, count_count
    agg_throughput = 0
    for e in record_sum.iterkeys():
      agg_throughput += record_sum[e] / (record_count[e] * 6)
    latency = (split_sum/split_count if split_count > 0 else 0) + (count_sum/count_count if count_count > 0 else 0)
    return (latency, agg_throughput)
  else:
    return (-1, -1)

class ExpResult:
  runtime = 0.0
  min_ram_gb = -1.0
  memcached_latency_us = -1.0
  storm_latency_us = -1
  storm_throughput = -1
  task = ""
  exp_start = ""
  reads = ""
  writes = ""
  rmem_gb = -1
  bw_gbps = -1
  latency_us = -1
  e2e_latency_us = 0
  inject = -1
  trace = -1
  trace_dir = ""
  slowdown_cdf = ""
  def get(self):
    if self.task == "memcached":
      return str(self.runtime) + ":" + str(self.memcached_latency_us)
    elif self.task == "storm":
      return str(self.storm_latency_us) + ":" + str(self.storm_throughput)
    else:
      return self.runtime

  def __str__(self):
    return "ExpStart: %s  Task: %s  RmemGb: %s  BwGbps: %s  LatencyUs: %s  E2eLatencyUs: %s  Inject: %s  Trace: %s  SldCdf: %s  MinRamGb: %s  Runtime: %s  MemCachedLatencyUs: %s  StormLatencyUs: %s  StormThroughput: %s  Reads: %s  Writes: %s  TraceDir: %s" % (self.exp_start, self.task, self.rmem_gb, self.bw_gbps, self.latency_us, self.e2e_latency_us, self.inject, self.trace, self.slowdown_cdf, self.min_ram_gb, self.runtime, self.memcached_latency_us, self.storm_latency_us, self.storm_throughput, self.reads, self.writes, self.trace_dir)

def run_exp(task, rmem_gb, bw_gbps, latency_us, e2e_latency_us, inject, trace, slowdown_cdf, profile = False, memcached_size=25):
  global memcached_kill_loadgen_on
  result = ExpResult()
  result.exp_start = str(datetime.datetime.now())
  result.task = task
  result.rmem_gb = rmem_gb
  result.bw_gbps = bw_gbps
  result.latency_us = latency_us
  result.e2e_latency_us = e2e_latency_us
  result.inject = inject
  result.trace = trace
  result.slowdown_cdf = slowdown_cdf

  min_ram = 0

  clean_existing_rmem(bw_gbps)

  setup_rmem(rmem_gb, bw_gbps, latency_us, e2e_latency_us, inject, trace, slowdown_cdf, task)

  if trace:
    log_trace()

  master = get_master()

  banner("Running app")
  if task == "wordcount":
    run("/root/ephemeral-hdfs/bin/hadoop fs -rmr /wikicount")
    start_time = time.time()  
    run("/root/spark/bin/spark-submit --class \"WordCount\" --master \"spark://%s:7077\" \"/root/disaggregation/apps/WordCount_spark/target/scala-2.10/simple-project_2.10-1.0.jar\" \"hdfs://%s:9000/wiki/\" \"hdfs://%s:9000/wikicount\"" % (master, master, master) )
    time_used = time.time() - start_time

  elif task == "terasort" or task == "wordcount-hadoop":
    run("/root/ephemeral-hdfs/bin/start-mapred.sh")
    run("/root/ephemeral-hdfs/bin/hadoop dfs -rmr /hadoopoutput")
    start_time = time.time()
    if profile:
      mem_monitor_start()
    if task == "terasort":
      run("/root/ephemeral-hdfs/bin/hadoop jar /root/disaggregation/apps/hadoop_terasort/hadoop-examples-1.0.4.jar terasort -Dmapred.map.tasks=20 -Dmapred.reduce.tasks=10 -Dmapreduce.map.java.opts=-Xmx25000 -Dmapreduce.reduce.java.opts=-Xmx25000 -Dmapreduce.map.memory.mb=26000 -Dmapreduce.reduce.memory.mb=26000 -Dmapred.reduce.slowstart.completed.maps=1.0 /sortinput /hadoopoutput")
    else:
      run("/root/ephemeral-hdfs/bin/hadoop jar /root/disaggregation/apps/hadoop_terasort/hadoop-examples-1.0.4.jar wordcount -Dmapred.map.tasks=10 -Dmapred.reduce.tasks=5 -Dmapreduce.map.java.opts=-Xmx8000 -Dmapreduce.reduce.java.opts=-Xmx7000 -Dmapreduce.map.memory.mb=8000 -Dmapreduce.reduce.memory.mb=7000 -Dmapred.reduce.slowstart.completed.maps=1.0 /wiki /hadoopoutput")
    if profile:
      min_ram = mem_monitor_stop()
      result.min_ram_gb = min_ram
    time_used = time.time() - start_time
    run("/root/ephemeral-hdfs/bin/stop-mapred.sh")
    run("/root/ephemeral-hdfs/bin/hadoop dfs -rmr /mnt")
    run("/root/ephemeral-hdfs/bin/hadoop dfs -rmr /hadoopoutput")
    slaves_run("rm -rf /mnt/ephemeral-hdfs/taskTracker/root/jobcache/*; rm -rf /mnt2/ephemeral-hdfs/taskTracker/root/jobcache/*; rm -rf /mnt99/taskTracker/root/jobcache/*; rm -rf /mnt/ephemeral-hdfs/mapred/local/taskTracker/root/jobcache/*; rm -rf /mnt2/ephemeral-hdfs/mapred/local/taskTracker/root/jobcache/*;  rm -rf /mnt99/mapred/local/taskTracker/root/jobcache/*")

  elif task == "graphlab":
    all_run("rm -rf /mnt2/netflix_m/out")
    start_time = time.time()
    if profile:
      mem_monitor_start()  
    run("mpiexec -n 5 -hostfile /root/spark-ec2/slaves /root/disaggregation/apps/collaborative_filtering/als --matrix /mnt2/netflix_m/ --max_iter=3 --ncpus=6 --minval=1 --maxval=5 --predictions=/mnt2/netflix_m/out/out")
    if profile: 
      min_ram = mem_monitor_stop()
      result.min_ram_gb = min_ram     
    time_used = time.time() - start_time

  elif task == "memcached":
    slaves_run("memcached -d -m 26000 -u root")
    set_memcached_size(memcached_size)
    run("/root/spark-ec2/copy-dir /root/disaggregation/apps/memcached/jars; /root/spark-ec2/copy-dir /root/disaggregation/apps/memcached/workloads")
    thrd = threading.Thread(target=memcached_kill_loadgen, args=(time.time() + 25 * 60,))
    thrd.start()
    slaves_run_parallel("cd /root/disaggregation/apps/memcached;java -cp jars/ycsb_local.jar:jars/spymemcached-2.7.1.jar:jars/slf4j-simple-1.6.1.jar:jars/slf4j-api-1.6.1.jar  com.yahoo.ycsb.LoadGenerator -load -P workloads/running")
    memcached_kill_loadgen_on = False
    thrd.join()
    all_run("rm /root/disaggregation/apps/memcached/results.txt")
    start_time = time.time()
    slaves_run_parallel("cd /root/disaggregation/apps/memcached;java -cp jars/ycsb.jar:jars/spymemcached-2.7.1.jar:jars/slf4j-simple-1.6.1.jar:jars/slf4j-api-1.6.1.jar  com.yahoo.ycsb.LoadGenerator -t -P workloads/running")
    result.memcached_latency_us = slaves_get_memcached_avg_latency()
    time_used = time.time() - start_time
    slaves_run("killall memcached")

  elif task == "storm":
    storm_start()
    time.sleep(10)
    run("/root/apache-storm-0.9.5/bin/storm kill test")
    time.sleep(90)
    start_time = time.time()
    run("/root/apache-storm-0.9.5/bin/storm jar /root/disaggregation/apps/storm/storm-starter-0.9.5-SNAPSHOT-jar-with-dependencies.jar storm.starter.WordCountTopology test")
    time.sleep(900)
    run("/root/apache-storm-0.9.5/bin/storm kill test")
    time_used = time.time() - start_time
    time.sleep(20)
    storm_stop()
    get_storm_trace()
    (latency, throughput) = get_storm_perf()
    result.storm_latency_us = latency
    result.storm_throughput = throughput

  if trace:
    result.trace_dir = collect_trace(task)

  if bw_gbps >= 0:
    (reads, writes) = get_rw_bytes()
    print "Remote Reads:"
    print reads
    print "Remote Writes:"
    print writes
    result.reads = str(reads).replace(" ", "")
    result.writes = str(writes).replace(" ", "")

  clean_existing_rmem(bw_gbps)

  print "Execution time:" + str(time_used) + " Min Ram:" + str(min_ram)
  result.runtime = time_used
  log(str(result), level = 1)

  if trace:
    with open(result.trace_dir + "/traceinfo.txt", "w") as f:
      f.write(" ".join(sys.argv) + "\n")
      f.write(str(result) + "\n")
  return result

def teragen(size):
  num_record = size * 1024 * 1024 * 1024 / 100
  master = get_master()
  run("/root/ephemeral-hdfs/bin/start-mapred.sh")
  run("/root/ephemeral-hdfs/bin/hadoop dfs -rmr /sortinput")
  run("/root/ephemeral-hdfs/bin/hadoop jar /root/disaggregation/apps/hadoop_terasort/hadoop-examples-1.0.4.jar teragen -Dmapred.map.tasks=20 %d hdfs://%s:9000/sortinput" % (num_record, master))
  run("/root/ephemeral-hdfs/bin/stop-mapred.sh")

def terasort_prepare_and_run(opts, size, bw_gb, latency_us, inject):
  run("/root/ephemeral-hdfs/bin/hadoop dfs -rmr /mnt")
  run("/root/ephemeral-hdfs/bin/hadoop dfs -rmr /sortinput")
  run("/root/ephemeral-hdfs/bin/hadoop dfs -rmr /sortoutput")
  teragen(opts.teragen_size)
  return run_exp("terasort", opts.remote_memory, bw_gb, latency_us, 0, inject, False, opt.cdf, profile = True)

def terasort_vary_size(opts):
  sizes = [180, 150, 120, 90, 60, 30]

  confs = [] #(inject, latency, bw, size)
  for s in sizes:
    confs.append((False, 0, 0, s))
    confs.append((True, 1, 40, s))


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

def disk_vary_size(opts):
  if opts.task == "graphlab" or opts.task == "memcached":
    run("/root/ephemeral-hdfs/bin/stop-all.sh")
    run("/root/spark/sbin/stop-all.sh")


  #sizes = [3, 6, 9, 12, 15, 18, 21, 24, 27]
  sizes = [6]
  rmems = [0.7]

  banner("Prepare input data")
  if opts.task == "graphlab":
    for s in sizes:
      slaves_run_parallel("python /root/disaggregation/rmem/trim_file.py /mnt2/netflix_mm %d /mnt2/nf%d.txt" % (s, s), master = True)

  confs = [] #(inject, latency, bw, size, rmem)
  for s in sizes:
    for rmem in rmems:
      confs.append((False, -1, -1, s, rmem))
      #confs.append((True, 1, 40, s, rmem))

  results = {}
  for conf in confs:
    results[conf] = []

  for i in range(0, opts.iter):
    for conf in confs:
      print "Running iter %d, conf %s" % (i, str(conf))
      if opts.task == "graphlab":
        all_run("rm /mnt2/netflix_m/netflix_mm; mkdir -p /mnt2/netflix_m; ln -s /mnt2/nf%d.txt /mnt2/netflix_m/netflix_mm" % (conf[3]))
      elif opts.task == "wordcount":
        wordcount_prepare(conf[3])
      time = run_exp(opts.task, conf[4] * 29.4567, conf[2], conf[1], 0, conf[0], False, opt.cdf, memcached_size = conf[3]).get()
      results[conf].append(time)


  log("\n\n\n")
  log("================== Started exp at:%s ==================" % str(datetime.datetime.now()))
  log('Argument %s' % str(sys.argv))

  for conf in results:
    result_str = "Conf: %s Result: %s" % (str(conf), ",".join(map(str, results[conf])))
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

def storm_install():
  run("cd /root; wget http://mirror.metrocast.net/apache/zookeeper/stable/zookeeper-3.4.6.tar.gz; tar xzf zookeeper-3.4.6.tar.gz; rm zookeeper-3.4.6.tar.gz")
  zoo_cfg = "tickTime=2000\ninitLimit=10\nsyncLimit=5\ndataDir=/mnt2/zookeeper\nclientPort=2181"
  with open("/root/zookeeper-3.4.6/conf/zoo.cfg", "w") as zoo_cfg_file:
    zoo_cfg_file.write(zoo_cfg)
  
  run("cd /root; wget http://mirror.sdunix.com/apache/storm/apache-storm-0.9.5/apache-storm-0.9.5.tar.gz; tar xzvf apache-storm-0.9.5.tar.gz; rm apache-storm-0.9.5.tar.gz")

def storm_start():
  run("/root/zookeeper-3.4.6/bin/zkServer.sh start")
  time.sleep(4)
  run("/root/apache-storm-0.9.5/bin/storm nimbus &")
  time.sleep(4)
  run("/root/apache-storm-0.9.5/bin/storm ui &")
  time.sleep(4)
  slaves_run("/root/apache-storm-0.9.5/bin/storm supervisor > /dev/null < /dev/null &")
  
def storm_stop():
  slaves_run("pid=\$(jps | grep supervisor | cut -d ' ' -f 1);kill \$pid")
  run("pid=$(jps | grep core | cut -d ' ' -f 1);kill $pid")
  run("pid=$(jps | grep nimbus | cut -d ' ' -f 1);kill $pid")
  run("/root/zookeeper-3.4.6/bin/zkServer.sh stop")

def graphlab_prepare(size_gb = 20):
  cmd = ('''
    cd /mnt2; 
    rm netflix_mm; 
    wget -q http://www.select.cs.cmu.edu/code/graphlab/datasets/netflix_mm;
    cat netflix_mm | sed -e '1,3d' >> temp.txt;
    mv temp.txt netflix_mm;
    rm -rf netflix_m; 
    mkdir netflix_m; 
    cd netflix_m;
    python /root/disaggregation/rmem/trim_file.py /mnt2/netflix_mm %s /mnt2/netflix_m/netflix_mm; 
  ''' % size_gb).replace("\n"," ")
  slaves_run_parallel(cmd, master = True)

def wordcount_prepare(size=125):
# run("mkdir -p /root/ssd; mount /dev/xvdg /root/ssd")
  run("/root/ephemeral-hdfs/bin/hadoop dfsadmin -safemode leave")
  run("/root/ephemeral-hdfs/bin/hadoop fs -rmr /wiki")
# run("/root/ephemeral-hdfs/bin/hadoop fs -put /root/ssd/wiki/f" + str(size) + "g.txt /wiki")
  run("/root/ephemeral-hdfs/bin/hadoop fs -mkdir /wiki")
  run("/root/ephemeral-hdfs/bin/start-mapred.sh")
  src = " ".join( ["s3n://petergao/wiki_raw/w-part{0:03}".format(i) for i in range(0, size)])
  run("/root/ephemeral-hdfs/bin/hadoop distcp %s /wiki/" % src)
  run("/root/ephemeral-hdfs/bin/stop-mapred.sh")

def storm_prepare():
  master = get_master()
  storm_cfg = '''storm.zookeeper.servers:
       - "%s"
storm.local.dir: "/mnt2/storm"
storm.log.dir: "/mnt2/storm/log"
nimbus.host: "%s"
supervisor.slots.ports:
      - 6700
      - 6701
      - 6702
      - 6703
ui.port: 8081''' % (master, master)
  with open("/root/apache-storm-0.9.5/conf/storm.yaml", "w") as storm_cfg_file:
    storm_cfg_file.write(storm_cfg)

  run("/root/spark-ec2/copy-dir /root/zookeeper-3.4.6; /root/spark-ec2/copy-dir /root/apache-storm-0.9.5")

 
  run("/root/spark-ec2/copy-dir /root/s3cmd; /root/spark-ec2/copy-dir /root/.s3cfg")
  slaves_run("rm -rf /mnt2/wikitmp; mkdir -p /mnt2/wikitmp")
  slaves = get_slaves()
  file_ids = [[] for s in slaves]
  for i in range(0, 125):
    file_ids[i%len(slaves)].append('{0:03}'.format(i))
  cmds = [ " ".join(map(lambda id : "/root/s3cmd/s3cmd get s3://petergao/wiki_raw/w-part%s /mnt2/wikitmp/w-part%s;" % (id, id),ids)) for ids in file_ids ]
  cmds = [ cmd + " mkdir -p /mnt2/storm; cat /mnt2/wikitmp/* > /mnt2/storm/input.txt; rm -rf /mnt2/wikitmp" for cmd in cmds]

  global bash_run_counter

  def ssh(machine, cmd, counter):
    command = "ssh " + machine + " '" + cmd + "' &> /mnt/local_commands/cmd_" + str(counter) + ".log"
    print "#######Running cmd:" + command
    os.system(command)
    print "#######Server " + machine + " command finished"

  if not os.path.exists("/mnt/local_commands"):
    os.system("mkdir -p /mnt/local_commands")

  threads = []
  for i in range(0, len(slaves)):
    s = slaves[i]
    t = threading.Thread(target=ssh, args=(s, cmds[i], bash_run_counter,))
    threads.append(t)
    bash_run_counter += 1
  [t.start() for t in threads]
  [t.join() for t in threads]
  print "Finished loading data"


def succinct_install():
  run("cd /root; git clone git@github.com:pxgao/succinct-cpp.git")
  run("/root/spark-ec2/copy-dir /root/succinct-cpp")
  run("/root/spark/sbin/slaves.sh /root/succinct-cpp/ec2/install_thrift.sh")

def reconfig_hdfs():
  run("/root/ephemeral-hdfs/bin/stop-all.sh")
  slaves_run("rm -rf /mnt/ephemeral-hdfs/*")
  slaves_run("rm -rf /mnt2/ephemeral-hdfs/*")
  run("/root/spark-ec2/copy-dir /root/ephemeral-hdfs/conf")
  run("/root/ephemeral-hdfs/bin/hadoop namenode -format")
  run("/root/ephemeral-hdfs/bin/start-dfs.sh")
  #.....you need to manually modify the conf files

def execute(opts):

  log("\n\n\n", level = 1)
  confs = [] #inject, latency_us, bw_gbps, rmem_gb, cdf, e2e_latency
  if opts.vary_latency:
    confs.append((False, 0, 0, opts.remote_memory, opts.cdf, 0))
    latencies = [1, 5, 10]
    bws = [100, 40, 10]
    for l in latencies:
      for b in bws:
        confs.append((True, l, b, opts.remote_memory, opts.cdf, 0))
  elif opts.vary_latency_40g:
    latency_40g = [1, 5, 10, 20, 40, 60, 80, 100]
    for l in latency_40g:
      confs.append((True, l, 40, opts.remote_memory, opts.cdf, 0))
  elif opts.vary_bw_5us:
    bw_5us = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
    for b in bw_5us:
      confs.append((True, 5, b, opts.remote_memory, opts.cdf, 0))                  
  elif opts.vary_remote_mem:
    local_rams = map(lambda x: x/10.0, range(1,10))
    local_rams.append(0.999)
    for r in local_rams:
      confs.append((True, 1, 40, (1-r) * 29.45, opts.cdf, 0))
  elif opts.slowdown_cdf_exp:
    confs.append((True, opts.latency, opts.bandwidth, opts.remote_memory, opts.task, 0))
    confs.append((True, opts.latency, opts.bandwidth, opts.remote_memory, "", 0))
  elif opts.vary_e2e_latency:
    e2e_latency = [0, 1, 5, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
    for el in e2e_latency:
      confs.append((False, 0, 0, opts.remote_memory, opts.cdf, el))
  else:
    confs.append((opts.inject, opts.latency, opts.bandwidth, opts.remote_memory, opts.task, 0))
 
  results = {}
  for conf in confs:
    results[conf] = []

  for i in range(0, opts.iter):
    for conf in confs:
      print "Running iter %d, conf %s" % (i, str(conf))
      time = run_exp(opts.task, conf[3], conf[2], conf[1], conf[5], conf[0], opts.trace, conf[4]).get()
      results[conf].append(time)


  log("\n\n\n")
  log("================== Started exp at:%s ==================" % str(datetime.datetime.now()))
  log('Argument %s' % str(sys.argv))

  for conf in results:
    result_str = "Conf: %s Result: %s" % (" ".join(map(str, conf)), " ".join(map(str, results[conf])))
    log(result_str)
    print result_str

def stop_tachyon():
  run("/root/tachyon/bin/tachyon-stop.sh")
  run("/root/ephemeral-hdfs/bin/hadoop dfs -rmr /tachyon")

def update_kernel():
  all_run("yum install kernel-devel -y; yum install kernel -y", background=True)

def install_mosh():
  run("sudo yum --enablerepo=epel install -y mosh")


def install_s3cmd():
  run("cd ~; git clone https://github.com/pxgao/s3cmd.git")

def install_all():
  update_kernel()
  slaves_run("mkdir -p /root/disaggregation/rmem/.remote_commands")
  install_blktrace()
  graphlab_install()
  memcached_install()
  storm_install()
  install_mosh()
  install_s3cmd()

def prepare_env():
  stop_tachyon()
  turn_off_os_swap()
  sync_rmem_code()
  update_hadoop_conf()
  mkfs_xvdc_ext4()
  run("mkdir -p /mnt/local_commands")

def prepare_all(opts):
  prepare_env()
  teragen(opts.teragen_size)
  graphlab_prepare()
  wordcount_prepare()


def main():
  opts = parse_args()
  run_exp_tasks = ["wordcount", "wordcount-hadoop", "terasort", "graphlab", "memcached", "storm"]
  

  if opts.disk_vary_size:
    disk_vary_size(opts) 
  elif opts.task in run_exp_tasks:
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
  elif opts.task == "storm-install":
    storm_install()
  elif opts.task == "storm-prepare":
    storm_prepare()
  elif opts.task == "prepare-env":
    prepare_env()
  elif opts.task == "prepare-all":
    prepare_all(opts)
  elif opts.task == "install-all":
    install_all()
  elif opts.task == "reconfig-hdfs":
    reconfig_hdfs()

  elif opts.task == "init-rmem":
    setup_rmem(5, 40, 10, 0, True, False, "wordcount", opts.task)
  elif opts.task == "exit-rmem":
    clean_existing_rmem(40) 
  elif opts.task == "sync-rmem-code":
    sync_rmem_code()

  elif opts.task == "reconfig-hdfs":
    reconfig_hdfs()
  elif opts.task == "storm-stop":
    storm_stop()
  elif opts.task == "storm-start":
    storm_start()
  elif opts.task == "s3cmd-install":
    install_s3cmd()
  elif opts.task == "test":
    print get_id_name_addr()
  else:
    print "Unknown task %s" % opts.task

if __name__ == "__main__":
  main()
