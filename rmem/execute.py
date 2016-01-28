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
import os.path
import time
from ec2_utils import *
import datetime
import sys
import xml.etree.ElementTree as etree
from xml.dom import minidom
import threading
import numpy as np
from memcached_workload import *

opts = None

def parse_args():
  parser = OptionParser(usage="execute.py [options]")
 
  parser.add_option("--task", help="Task to be done")
  parser.add_option("-r", "--remote-memory", type="float", default=22.09, help="Remote memory size in GB")
  parser.add_option("-b", "--bandwidth", type="float", default=40, help="Bandwidth in Gbps")
  parser.add_option("-l", "--latency", type="int", default=5, help="Latency in us")
  parser.add_option("-i", "--inject", action="store_true", default=False, help="Whether to inject latency")
  parser.add_option("--cdf", type="string", default="", help="Inject latency with slowdown")
  parser.add_option("-t", "--trace", action="store_true", default=False, help="Whether to get trace")
  parser.add_option("--profile-io", action="store_true", default=False, help="Get an IO trace")
  parser.add_option("--vary-both-latency-bw", action="store_true", default=False, help="Experiment on different latency bandwidth combinations")
  parser.add_option("--vary-e2e-latency", action="store_true", default=False, help="Experiment on different end to end latency")
  parser.add_option("--vary-latency", action="store_true", default=False, help="Experiment on different latency with 40G bandwidth")
  parser.add_option("--disk-vs-ram", action="store_true", default=False, help="Compare performance between disk and ram")
  parser.add_option("--vary-bw", action="store_true", default=False, help="Experiment on different bw with 5us latency")
  parser.add_option("--vary-remote-mem", action="store_true", default=False, help="Experiment that varies percentage of remote memory with 40G/5us latency injected")
  parser.add_option("--inject-test", action="store_true", default=False, help="Test latency injection")
  parser.add_option("--inject-40g-3us", action="store_true", default=False, help="Inject 40g/3us latency")
  parser.add_option("--slowdown-cdf-exp", action="store_true", default=False, help="Variable latency injected with given CDF file")
  parser.add_option("--dstat", action="store_true", default=False, help="Collect dstat trace")
  parser.add_option("--disk-vary-size", action="store_true", default=False, help="Use disk as swap, vary input size")
  parser.add_option("--iter", type="int", default=1, help="Number of iterations")
  parser.add_option("--spark-mem", type="float", default=25, help="Spark executor memory")
  parser.add_option("--spark-cores-max", type="int", default=40, help="Spark cores")
  parser.add_option("--teragen-size", type="float", default=125.0, help="Sort input data size (GB)")
  parser.add_option("--es-data", type="float", default=0.2, help="ElasticSearch data per server (GB)")
  parser.add_option("--no-sit", action="store_true", default=False, help="Don't run special instrumentation")

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
  inject_int = 1 if inject and slowdown_cdf == "" else 0
  trace_int = 1 if trace else 0

  if bw_gbps < 0:
    rmem_mb = int(rmem_gb * 1024)
    install_rmem = '''
      cd /root/disaggregation/rmem
      mkdir -p tmpfs
      mount -t tmpfs -o size=%dm tmpfs ./tmpfs/
      fallocate -l %dm ./tmpfs/a.img

      swapoff /mnt2/swapdisk/swap
      rm -rf /mnt2/swapdisk/swap
      mkdir -p /mnt2/swapdisk
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
      insmod rmem.ko npages=%d get_record=%d;
      mkswap /dev/rmem0;
      swapon /dev/rmem0;
      echo 0 > /proc/sys/fs/rmem/read_bytes;
      echo 0 > /proc/sys/fs/rmem/write_bytes;

      echo %d > /proc/sys/fs/rmem/bandwidth_bps;
      echo %d > /proc/sys/fs/rmem/latency_ns;
      echo %d > /proc/sys/fs/rmem/end_to_end_latency_ns;
      echo %d > /proc/sys/fs/rmem/inject_latency;

      pid=$(ps aux | grep kswapd0 | grep -v grep | tr -s ' ' | cut -d ' ' -f 2)
      taskset -cp 7 $pid
      ''' % (remote_page, trace_int, bandwidth_bps, latency_ns, e2e_latency_ns, inject_int)
    slaves_run_bash(install_rmem)

    if slowdown_cdf != "":
      assert(os.path.exists(slowdown_cdf))
      run("/root/spark-ec2/copy-dir /root/disaggregation/rmem/fcts")
      slaves_run("cd /root/disaggregation/rmem; cat %s | python convert_fct_to_ns.py > fcts.txt ; cat fcts.txt | while read -r line; do echo \$line > /proc/rmem_cdf; done; diff /proc/rmem_cdf fcts.txt" % slowdown_cdf) 


def dstat():
  banner("Running dstats")
  slaves_run("rm -rf /mnt/dstat; rm -rf /mnt/bwm")
  for s in get_slaves():
    nc = int(commands.getstatusoutput("nproc")[1])
    if nc <= 8:
      run("ssh -f %s \"nohup dstat -cndgt -N eth0 --output /mnt/dstat 2>&1 > /dev/null < /dev/null &\"" % s)
    else:
      run("ssh -f %s \"nohup dstat -cndgt -N eth0 -C 0,1,2,3,4,5,6,7,total --output /mnt/dstat 2>&1 > /dev/null < /dev/null &\"" % s)
    #run("ssh -f %s \"nohup bwm-ng -o csv -t 1000 -I eth0 -T rate > /mnt/bwm 2>&1 < /dev/null &\"" % s)

def collect_dstat(task = "task"):
  banner("Collecting dstat trace")
  slaves_run("killall -SIGINT dstat")
  #slaves_run("killall -SIGINT bwm-ng")
  result_dir = "/mnt/dstat/%s_%s" % (task, run_and_get("date +%y%m%d%H%M%S")[1])
  run("mkdir -p %s" % result_dir)
  slaves = get_slaves()
  for i in range(len(slaves)):
    s = slaves[i]
    scp_from("/mnt/dstat", "%s/%s-dstat.txt" % (result_dir, i), s)
    #scp_from("/mnt/bwm", "%s/%s-bwm.txt" % (result_dir, i), s)
  return result_dir

def log_trace():
  banner("log trace")
  get_disk_mem_log = '''
    rm -rf /mnt2/rmem_log
    mkdir -p /mnt2/rmem_log
    cd /mnt2/rmem_log

    if [ -z "$(mount | grep /sys/kernel/debug)" ]
    then
      mount -t debugfs debugfs /sys/kernel/debug
    fi

    start_time=$(date +%s%N)
    echo ${start_time:0:${#start_time}-3} > .metadata
  
    blktrace -a issue -d /dev/xvda1 /dev/xvdb /dev/xvdc -D . &
  
    tcpdump -i eth0 2>&1 | python /root/disaggregation/rmem/tcpdump2flow.py > .nic &

    /root/disaggregation/rmem/fetch /proc/rmem_log /mnt2/rmem_log/rmem_dump &

    pid=$(ps aux | grep fetch | grep -v grep | tr -s ' ' | cut -d ' ' -f 2)
    taskset -cp 6 $pid
  '''
  slaves_run_bash(get_disk_mem_log, silent = True, background = True)

def collect_trace(task):
  banner("collect trace")
  slaves_run("killall -SIGINT fetch;killall -SIGINT tcpdump;killall -SIGINT blktrace")
  time.sleep(25)
  slaves_run_parallel("/root/disaggregation/rmem/parse /mnt2/rmem_log/rmem_dump /mnt2/rmem_log/rmem_log.txt")
  
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



def cpuset():
  cmd = '''umount /mnt/cpuset
  rm -rf /mnt/cpuset
  mkdir -p /mnt/cpuset
  mount -t cpuset none /mnt/cpuset/
  mkdir -p /mnt/cpuset/sw
  mkdir -p /mnt/cpuset/other
  echo 0 > /mnt/cpuset/sw/mems
  echo 0 > /mnt/cpuset/other/mems
  echo 7 > /mnt/cpuset/sw/cpus
  echo 0-6 > /mnt/cpuset/other/cpus
  echo 0 > /mnt/cpuset/other/sched_load_balance
  for T in $(cat /mnt/cpuset/tasks)
  do
    /bin/echo $T | tee /mnt/cpuset/other/tasks
  done'''
  slaves_run_bash(cmd)

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

def get_overflow():
  overflows = []
  slaves = get_slaves()
  for s in slaves:
    of = int(run_and_get("ssh root@%s \"cat /proc/sys/fs/rmem/overflow\"" % s)[1].replace("\n",""))
    overflows.append(of)
  return overflows

exp_finished = False
io_trace = []
def profile_io():
  global exp_finished
  global io_trace
  next_log_time = time.time()
  while not exp_finished:
    if time.time() > next_log_time:
      (r, w) = get_rw_bytes()
      io = np.mean(r + w)
      print "====================io %s=================" % io
      io_trace.append(io)
      next_log_time += 20

def profile_io_start():
  global exp_finished
  global io_trace
  exp_finished = False
  io_trace = []
  thrd = threading.Thread(target=profile_io)
  thrd.start()

def profile_io_end():
  global exp_finished
  global io_trace
  exp_finished = True
  time.sleep(1)
  return io_trace


def sync_rmem_code():
  banner("Sync rmem code")
  run("cd /root/disaggregation/rmem; /root/spark-ec2/copy-dir .")
  slaves_run("cd /root/disaggregation/rmem; make")

def mkfs_xvdc_ext4():
  dev = ""
  devs = ["xvdc", "xvdf"]
  for d in devs:
    if d in os.popen("ls /dev/%s" % d).read():
      dev = d
      break
  if dev == "":
    assert(False)
  all_run("umount /mnt2;mkfs.ext4 /dev/%s; mount /dev/%s /mnt2" % (dev, dev))
  

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
  total_latency = 0
  total_throughput = 0
  slaves = get_slaves()
  for s in slaves:
    r = run_and_get("ssh %s \"cat /root/disaggregation/apps/memcached/results.txt | grep AverageLatency\"" % s)[1]
    v = r.replace("[GET] AverageLatency, ","")
    if "us" in v:
      total_latency += float(v.replace("us",""))
    elif "ms" in v:
      total_latency += float(v.replace("ms","")) * 1000
    rt = run_and_get("ssh %s \"cat /root/disaggregation/apps/memcached/results.txt | grep Throughput\"" % s)[1]
    vt = rt.replace("[OVERALL] Throughput(ops/sec), ", "")
    total_throughput += float(vt)
  return (total_latency / len(slaves), total_throughput / len(slaves))

def get_bdb_query(id):
  QUERY_3a_HQL = """SELECT sourceIP,
      sum(adRevenue) as totalRevenue,
      avg(pageRank) as pageRank
    FROM
      rankings R JOIN
      (SELECT sourceIP, destURL, adRevenue
       FROM uservisits UV
       WHERE UV.visitDate > '1980-01-01'
       AND UV.visitDate < '1980-04-01')
       NUV ON (R.pageURL = NUV.destURL)
    GROUP BY sourceIP
    ORDER BY totalRevenue DESC
    LIMIT 1""".replace("\n", " ")

  QUERY_2a_HQL = "SELECT SUBSTR(sourceIP, 1, 8), SUM(adRevenue) FROM uservisits GROUP BY SUBSTR(sourceIP, 1, 8)"

  if id == "2a":
    return QUERY_2a_HQL
  elif id == "3a":
    return QUERY_3a_HQL
  else:
    raise "invalid query id"


def get_storm_trace():
  slaves = get_slaves()
  for s in slaves:
    size = run_and_get("ssh %s \"ls -la /mnt2/storm/log/metrics.log | awk '{ print \$5}'\"" % s)[1]
    if(int(size) > 0):
      run("rm -rf /mnt2/metrics.log")
      scp_from("/mnt2/storm/log/metrics.log", "/mnt2/metrics.log", s)
  slaves_run("rm -rf /mnt2/storm/log/metrics.log")

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
  memcached_throughput = -1
  storm_latency_us = -1
  storm_throughput = -1
  es_throughput = -1
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
  io_trace = ""
  overflow = ""
  no_sid = ""
  spark_mem = ""
  def get(self):
    if self.task == "memcached":
      return str(self.runtime) + ":" + str(self.memcached_latency_us) + ":" + str(self.memcached_throughput)
    elif self.task == "storm":
      return str(self.storm_latency_us) + ":" + str(self.storm_throughput)
    elif self.task == "elasticsearch":
      return str(self.es_throughput)
    else:
      return self.runtime

  def __str__(self):
    return "ExpStart: %s  Task: %s  RmemGb: %s  BwGbps: %s  LatencyUs: %s  E2eLatencyUs: %s  Inject: %s  Trace: %s  SldCdf: %s  MinRamGb: %s  Runtime: %s  MemCachedLatencyUs: %s  MemCachedThroughput: %s  StormLatencyUs: %s  StormThroughput: %s  ESThroughput: %s  Reads: %s  Writes: %s  TraceDir: %s  IOTrace: %s  Overflow: %s" % (self.exp_start, self.task, self.rmem_gb, self.bw_gbps, self.latency_us, self.e2e_latency_us, self.inject, self.trace, self.slowdown_cdf, self.min_ram_gb, self.runtime, self.memcached_latency_us, self.memcached_throughput, self.storm_latency_us, self.storm_throughput, self.es_throughput, self.reads, self.writes, self.trace_dir, self.io_trace, self.overflow)

def run_exp(task, rmem_gb, bw_gbps, latency_us, e2e_latency_us, inject, trace, slowdown_cdf, profile_io, dstat_log, no_sit, spark_mem, profile = False, memcached_size=22):
  global memcached_kill_loadgen_on
  global opts
  start_time = [-1]

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
  result.no_sit = no_sit
  result.spark_mem = spark_mem

  min_ram = 0

  def app_start():
    start_time[0] = time.time()
    if profile:
      mem_monitor_start()
    if dstat_log:
      cpuset()
      dstat()
    if trace:
      log_trace()
    if profile_io:
      profile_io_start()


  def app_end():
    assert(start_time[0] > 0)
    result.runtime = time.time() - start_time[0]
    if profile:
      result.min_ram_gb = mem_monitor_stop()
    if dstat_log:
      dir = collect_dstat(task)
      print "dstat results in %s" % dir
      slaves_run("umount /mnt/cpuset")
    if profile_io:
      result.io_trace = str(profile_io_end())
    if trace:
      result.trace_dir = collect_trace(task)
      result.overflow = str(get_overflow())
      print "Overflow: %s" % result.overflow

  if not no_sit: 
    clean_existing_rmem(bw_gbps)

    setup_rmem(rmem_gb, bw_gbps, latency_us, e2e_latency_us, inject, trace, slowdown_cdf, task)


  master = get_master()

  banner("Running app")
  if task == "wordcount" or task == "terasort-spark":
    run("/root/ephemeral-hdfs/bin/hadoop fs -rmr /dfsresult")
    app_start()
    if task == "wordcount":
      run("/root/spark/bin/spark-submit --class \"WordCount\" --master \"spark://%s:7077\" --conf \"spark.executor.memory=%sm\" --conf \"spark.cores.max=%s\" \"/root/disaggregation/apps/WordCount_spark/target/scala-2.10/simple-project_2.10-1.0.jar\" \"/wiki/\" \"/dfsresult\"" % (master, int(spark_mem * 1024), opts.spark_cores_max) )
    elif task == "terasort-spark":
      run("/root/spark/bin/spark-submit --class \"TeraSort\" --master \"spark://%s:7077\" --conf \"spark.executor.memory=%sm\" --conf \"spark.cores.max=%s\" \"/root/disaggregation/apps/spark_terasort/target/scala-2.10/terasort_2.10-1.0.jar\" \"/sortinput/\" \"/dfsresult\"" % (master, int(spark_mem * 1024), opts.spark_cores_max) )
    app_end()

  elif task == "bdb":
    run("/root/ephemeral-hdfs/bin/hadoop fs -rmr /dfsresults")
    app_start() 
    query = get_bdb_query("3a") # 2a or 3a
    run("/root/spark/bin/spark-submit --class \"SparkSql\" --master \"spark://%s:7077\" --conf \"spark.executor.memory=%sm\" --conf \"spark.cores.max=%s\" \"/root/disaggregation/apps/Spark_Sql/target/scala-2.10/spark-sql_2.10-1.0.jar\" \"/dfsresults\" \"%s\"" % (master, int(spark_mem * 1024), opts.spark_cores_max, query) )
    app_end()

  elif task == "terasort" or task == "wordcount-hadoop":
    run("/root/ephemeral-hdfs/bin/start-mapred.sh")
    run("/root/ephemeral-hdfs/bin/hadoop dfs -rmr /dfsresult")
    app_start()
    if task == "terasort":
      run("/root/ephemeral-hdfs/bin/hadoop jar /root/disaggregation/apps/hadoop_terasort/hadoop-examples-1.0.4.jar terasort -Dmapred.map.tasks=20 -Dmapred.reduce.tasks=10 -Dmapreduce.map.java.opts=-Xmx25000 -Dmapreduce.reduce.java.opts=-Xmx25000 -Dmapreduce.map.memory.mb=26000 -Dmapreduce.reduce.memory.mb=26000 -Dmapred.reduce.slowstart.completed.maps=1.0 /sortinput /dfsresult")
    else:
      run("/root/ephemeral-hdfs/bin/hadoop jar /root/disaggregation/apps/hadoop_terasort/hadoop-examples-1.0.4.jar wordcount -Dmapred.map.tasks=10 -Dmapred.reduce.tasks=5 -Dmapreduce.map.java.opts=-Xmx8000 -Dmapreduce.reduce.java.opts=-Xmx7000 -Dmapreduce.map.memory.mb=8000 -Dmapreduce.reduce.memory.mb=7000 -Dmapred.reduce.slowstart.completed.maps=1.0 /wiki /dfsresult")
    run("/root/ephemeral-hdfs/bin/stop-mapred.sh")
    app_end()
    run("/root/ephemeral-hdfs/bin/hadoop dfs -rmr /mnt")
    run("/root/ephemeral-hdfs/bin/hadoop dfs -rmr /hadoopoutput")
    slaves_run("rm -rf /mnt/ephemeral-hdfs/taskTracker/root/jobcache/*; rm -rf /mnt2/ephemeral-hdfs/taskTracker/root/jobcache/*; rm -rf /mnt99/taskTracker/root/jobcache/*; rm -rf /mnt/ephemeral-hdfs/mapred/local/taskTracker/root/jobcache/*; rm -rf /mnt2/ephemeral-hdfs/mapred/local/taskTracker/root/jobcache/*;  rm -rf /mnt99/mapred/local/taskTracker/root/jobcache/*")

  elif task == "graphlab":
    all_run("rm -rf /mnt2/netflix_m/out")
    app_start()
    run("mpiexec -n 5 -hostfile /root/spark-ec2/slaves /root/disaggregation/apps/collaborative_filtering/als --matrix /mnt2/netflix_m/ --max_iter=3 --ncpus=6 --minval=1 --maxval=5 --predictions=/mnt2/netflix_m/out/out")
    app_end()

  elif task == "memcached" or task == "memcached-local":
    app_start()
    slaves_run("memcached -d -m 26000 -u root")
    set_memcached_size(memcached_size)
    run("/root/spark-ec2/copy-dir /root/disaggregation/apps/memcached/jars; /root/spark-ec2/copy-dir /root/disaggregation/apps/memcached/workloads")
    thrd = threading.Thread(target=memcached_kill_loadgen, args=(time.time() + 25 * 60,))
    thrd.start()
    print "Loadgen started at %s" % time.strftime("%c")
    slaves_run_parallel("cd /root/disaggregation/apps/memcached;java -cp jars/ycsb_local.jar:jars/spymemcached-2.7.1.jar:jars/slf4j-simple-1.6.1.jar:jars/slf4j-api-1.6.1.jar  com.yahoo.ycsb.LoadGenerator -load -P workloads/running")
    print "Loadgen finished at %s" % time.strftime("%c")
    memcached_kill_loadgen_on = False
    thrd.join()
    all_run("rm /root/disaggregation/apps/memcached/results.txt")
    if task == "memcached":
      slaves_run_parallel("cd /root/disaggregation/apps/memcached;java -cp jars/ycsb.jar:jars/spymemcached-2.7.1.jar:jars/slf4j-simple-1.6.1.jar:jars/slf4j-api-1.6.1.jar  com.yahoo.ycsb.LoadGenerator -t -P workloads/running")
    elif task == "memcached-local":
      slaves_run_parallel("cd /root/disaggregation/apps/memcached;java -cp jars/ycsb_local.jar:jars/spymemcached-2.7.1.jar:jars/slf4j-simple-1.6.1.jar:jars/slf4j-api-1.6.1.jar  com.yahoo.ycsb.LoadGenerator -t -P workloads/running")

    (result.memcached_latency_us, result.memcached_throughput) = slaves_get_memcached_avg_latency()
    slaves_run("killall memcached")
    app_end()

  elif task == "storm":
    storm_start()
    time.sleep(10)
    run("/root/apache-storm-0.9.5/bin/storm kill test")
    time.sleep(90)
    app_start()
    run("/root/apache-storm-0.9.5/bin/storm jar /root/disaggregation/apps/storm/storm-starter-topologies-0.9.5.jar storm.starter.WordCountTopology test")
    time.sleep(1800)
    run("/root/apache-storm-0.9.5/bin/storm kill test")
    time.sleep(20)
    storm_stop()
    app_end()
    get_storm_trace()
    (latency, throughput) = get_storm_perf()
    result.storm_latency_us = latency
    result.storm_throughput = throughput

  elif task == "timely":
    app_start()
    timely_run()
    app_end()

  elif task == "elasticsearch":
    app_start()
    elasticsearch_run()
    app_end()
    result.es_throughput = get_es_throughput()
  

  if bw_gbps >= 0 and not no_sit:
    (reads, writes) = get_rw_bytes()
    print "Remote Reads:"
    print reads
    print "Remote Writes:"
    print writes
    result.reads = str(reads).replace(" ", "")
    result.writes = str(writes).replace(" ", "")

  if not no_sit:
    clean_existing_rmem(bw_gbps)

  print "Execution time:" + str(result.runtime) + " Min Ram:" + str(min_ram)
  log(str(result), level = 1)

  if trace:
    with open(result.trace_dir + "/traceinfo.txt", "w") as f:
      f.write(" ".join(sys.argv) + "\n")
      f.write(str(result) + "\n")
    print "TraceDir: %s" % result.trace_dir
  return result

def teragen(size):
  num_record = size * 1024 * 1024 * 1024 / 100
  master = get_master()
  run("/root/ephemeral-hdfs/bin/start-mapred.sh")
  run("/root/ephemeral-hdfs/bin/hadoop dfs -rmr /sortinput")
  run("/root/ephemeral-hdfs/bin/hadoop jar /root/disaggregation/apps/hadoop_terasort/hadoop-examples-1.0.4.jar teragen -Dmapred.map.tasks=20 %d hdfs://%s:9000/sortinput" % (num_record, master))
  run("/root/ephemeral-hdfs/bin/stop-mapred.sh")

def terasort_spark_prepare(size, input_dir = "sortinput"):
  master = get_master()
  run("/root/ephemeral-hdfs/bin/hadoop dfs -rmr /sortinput")
  run("/root/spark/bin/spark-submit --class \"TeraGen\" --master \"spark://%s:7077\" \"/root/disaggregation/apps/spark_terasort/target/scala-2.10/terasort_2.10-1.0.jar\" %sg \"/%s\"" % (master, int(size), input_dir))


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


  sizes = [3, 6, 9, 12, 15]
  #sizes = [6]
  rmems = [0.75]

  banner("Prepare input data")
  if opts.task == "graphlab":
    for s in sizes:
      slaves_run_parallel("python /root/disaggregation/rmem/trim_file.py /mnt2/netflix_mm %d /mnt2/nf%d.txt" % (s, s), master = True)

  confs = [] #(inject, latency, bw, size, rmem)
  for s in sizes:
    for rmem in rmems:
      confs.append((False, -1, -1, s, rmem))
      confs.append((True, 5, 40, s, rmem))

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
      time = run_exp(opts.task, conf[4] * 29.4567, conf[2], conf[1], 0, conf[0], False, opts.cdf, False, False, False, opts.spark_mem, memcached_size = conf[3], profile = True).get()
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

def mount_disk():
  slaves_run("rm -rf /mnt2/swapdisk/; mkdir -p /mnt2/swapdisk; mkfs.ext4 /dev/xvdg; mount /dev/xvdg /mnt2/swapdisk")

def wordcount_prepare(size=125):
# run("mkdir -p /root/ssd; mount /dev/xvdg /root/ssd")
  run("/root/ephemeral-hdfs/bin/hadoop dfsadmin -safemode leave")
  run("/root/ephemeral-hdfs/bin/hadoop fs -rmr /wiki")
# run("/root/ephemeral-hdfs/bin/hadoop fs -put /root/ssd/wiki/f" + str(size) + "g.txt /wiki")
  run("/root/ephemeral-hdfs/bin/hadoop fs -mkdir /wiki")
  run("/root/ephemeral-hdfs/bin/start-mapred.sh")
  src = " ".join( ["s3n://petergao/wiki_raw/w-part{0:03}".format(i) for i in range(0, size)])
  run("/root/ephemeral-hdfs/bin/hadoop distcp -m 20  %s /wiki/" % src)
  run("/root/ephemeral-hdfs/bin/stop-mapred.sh")


def bdb_prepare():
  run("/root/ephemeral-hdfs/bin/hadoop dfsadmin -safemode leave")
  run("/root/ephemeral-hdfs/bin/hadoop fs -rmr /uservisits")
  run("/root/ephemeral-hdfs/bin/hadoop fs -rmr /rankings")
  run("/root/ephemeral-hdfs/bin/start-mapred.sh")
  run("/root/ephemeral-hdfs/bin/hadoop distcp -m 20 s3n://petergao/uservisits/ /uservisits/")
  run("/root/ephemeral-hdfs/bin/hadoop distcp -m 20 s3n://petergao/rankings/ /rankings/")
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
      - 6704
      - 6705
      - 6706
      - 6707
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


def install_elasticsearch():
  all_run("wget https://download.elasticsearch.org/elasticsearch/release/org/elasticsearch/distribution/rpm/elasticsearch/2.1.1/elasticsearch-2.1.1.rpm; rpm -ivh elasticsearch-2.1.1.rpm; rm elasticsearch-2.1.1.rpm")
  install_mvn()
  run("/usr/share/elasticsearch/bin/plugin install mobz/elasticsearch-head")
  #run("cd /root; git clone https://github.com/pxgao/YCSB.git; cd /root/YCSB; mvn clean package")
  #run("/root/spark-ec2/copy-dir /root/YCSB")
  es_bench()

def es_bench():
  slaves_run_parallel("yum install -y python27; wget https://bootstrap.pypa.io/get-pip.py; python27 get-pip.py; rm get-pip.py; pip install https://github.com/mkocikowski/esbench/archive/dev.zip", master = True)
  run("cd /root; git clone https://github.com/pxgao/esbench.git; cp -r /root/esbench /usr/lib/python2.7/dist-packages/; /root/spark-ec2/copy-dir /usr/lib/python2.7/dist-packages/esbench/")

def get_es_throughput():
  run("rm -rf /mnt/es_stats; mkdir -p /mnt/es_stats")
  throu = 0
  slaves = get_slaves()
  for i in range(len(slaves)):
    s = slaves[i]
    scp_from("/mnt/esbench_throughput", "/mnt/es_stats/t%s" % i, s)
    with open("/mnt/es_stats/t%s" % i) as f:
      throu += float(f.read())
  run("rm -rf /mnt/es_stats")
  return throu

def elasticsearch_prepare():
  global opts
  def get_elastic_conf(id):
    all = []#get_slaves()
    all.append(get_master())
    slaves = str([ s + ":9300" for s in all]).replace("'", "\"")
    addr = get_master() if id == 0 else get_slaves()[id-1]
    conf = '''cluster.name: ddc
node.name: ddc%s
node.master: %s
node.data: %s
network.host: %s
path.data: /mnt2/es/data
path.work: /mnt2/es/work
path.logs: /mnt2/es/logs
index.store.fs.memory.enabled: true
cache.memory.small_buffer_size: 4mb
cache.memory.large_cache_size: 4096mb
discovery.zen.ping.multicast.enabled: false
discovery.zen.ping.unicast.hosts: %s''' % (id, "true" if id == 0 else "false", "false" if id == 0 else "true", "0.0.0.0", slaves)
    return conf

  with open("/etc/elasticsearch/elasticsearch.yml", "w") as f:
    f.write(get_elastic_conf(0))

  for i in range(1, 6):
    with open("/mnt/elasticsearch.yml", "w") as f:
      f.write(get_elastic_conf(i))
    scp_to("/mnt/elasticsearch.yml", "/etc/elasticsearch/elasticsearch.yml", get_slaves()[i-1])
  run("rm /mnt/elasticsearch.yml")
  all_run("export ES_HEAP_SIZE=25g; rm -rf /mnt2/es; mkdir -p /mnt2/es/data; mkdir -p /mnt2/es/logs; mkdir -p /mnt2/es/work; chown elasticsearch:elasticsearch /mnt2/es/data; chown elasticsearch:elasticsearch /mnt2/es/logs; chown elasticsearch:elasticsearch /mnt2/es/work")

  #prepare data
  slaves_run_parallel("esbench run %smb --prepare" % int(opts.es_data * 1024))

def elasticsearch_run():
  slaves_run_parallel("service elasticsearch start", master = True)
  slaves_run_parallel("rm -rf /mnt/esbench_throughput; esbench run %smb" % int(opts.es_data * 1024))  
  all_run("service elasticsearch stop")



def update_hdfs_conf(new_temp = "/mnt/ephemeral-hdfs,/mnt2/ephemeral-hdfs", new_rep = 1, new_data = "/mnt/ephemeral-hdfs/data,/mnt2/ephemeral-hdfs/data"):
  with open('/root/ephemeral-hdfs/conf/core-site.xml', 'r') as core_file:
    core_file_content = core_file.read()
  updated_core_file_content = core_file_content.replace("<value>/mnt/ephemeral-hdfs</value>","<value>%s</value>" % new_temp)
  with open('/root/ephemeral-hdfs/conf/core-site.xml', 'w') as core_file:
    core_file.write(updated_core_file_content)

  with open('/root/ephemeral-hdfs/conf/hdfs-site.xml', 'r') as hdfs_file:
    hdfs_file_content = hdfs_file.read()
  updated_hdfs_file_content = hdfs_file_content.replace("<value>3</value>","<value>%s</value>" % new_rep).replace("<value>/mnt/ephemeral-hdfs/data</value>","<value>%s</value>" % new_data)
  with open('/root/ephemeral-hdfs/conf/hdfs-site.xml', 'w') as hdfs_file:
    hdfs_file.write(updated_hdfs_file_content)
  

def reconfig_hdfs():
  update_hdfs_conf()
  run("/root/ephemeral-hdfs/bin/stop-all.sh")
  slaves_run("rm -rf /mnt/ephemeral-hdfs/*")
  slaves_run("rm -rf /mnt2/ephemeral-hdfs/*")
  run("/root/spark-ec2/copy-dir /root/ephemeral-hdfs/conf")
  run("/root/ephemeral-hdfs/bin/hadoop namenode -format")
  run("/root/ephemeral-hdfs/bin/start-dfs.sh")
  #.....you need to manually modify the conf files

def execute(opts):
  spark_apps = ["wordcount", "terasort-spark", "bdb"]
  if opts.task in spark_apps:
    baseline = (False, 0, 0, opts.remote_memory, opts.cdf, 0, True, 25)
  else:
    baseline = (False, 0, 0, opts.remote_memory, opts.cdf, 0, False, 25)

  log("\n\n\n", level = 1)
  confs = [] #inject, latency_us, bw_gbps, rmem_gb, cdf, e2e_latency, no_sit, spark_mem

  if opts.inject_test:
    confs.append(baseline)
    confs.append((True, 5, 40, opts.remote_memory, opts.cdf, 0, False, 30 - opts.remote_memory))

  elif opts.inject_40g_3us:
    confs.append(baseline)
    confs.append((True, 3, 40, opts.remote_memory, opts.cdf, 0, False, 30 - opts.remote_memory))

  elif opts.vary_both_latency_bw:
    confs.append(baseline)
    latencies = [1, 5, 10]
    bws = [100, 40, 10]
    for l in latencies:
      for b in bws:
        confs.append((True, l, b, opts.remote_memory, opts.cdf, 0, False, 30 - opts.remote_memory))

  elif opts.vary_latency:
    latency_40g = [1, 5, 10, 20, 40]
    confs.append(baseline)
    for l in latency_40g:
      confs.append((True, l, 40, opts.remote_memory, opts.cdf, 0, False, 30 - opts.remote_memory))

  elif opts.vary_bw:
    bw_5us = [10, 20, 40, 60, 80, 100]
    confs.append(baseline)
    for b in bw_5us:
      confs.append((True, 5, b, opts.remote_memory, opts.cdf, 0, False, 30 - opts.remote_memory))                  

  elif opts.vary_remote_mem:
    local_rams = map(lambda x: x/10.0, range(1,10))
    local_rams.append(0.9999)
    for r in local_rams:
      confs.append((True, 5, 40, (1-r) * 29.45, opts.cdf, 0, False, r * 29.45 + 0.5))
      confs.append((False, 0, 10000, (1-r) * 29.45, opts.cdf, 0, False, r * 29.45 + 0.5))

  elif opts.slowdown_cdf_exp:
    rack_scale_file = "/root/disaggregation/rmem/fcts/fcts_tmrs_pfabric_%s.txt" % opts.task
    dc_scale_file = "/root/disaggregation/rmem/fcts/fcts_tm_pfabric_%s.txt" % opts.task
    confs.append((False, opts.latency, opts.bandwidth, opts.remote_memory, rack_scale_file, 0, False, 30 - opts.remote_memory))
    confs.append((False, opts.latency, opts.bandwidth, opts.remote_memory, dc_scale_file, 0, False, 30 - opts.remote_memory))
    #confs.append(baseline)


#  elif opts.vary_e2e_latency:
#    e2e_latency = [0, 1, 5, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
#    for el in e2e_latency:
#      confs.append((False, 0, 0, opts.remote_memory, opts.cdf, el))
#  elif opts.disk_vs_ram:
#    confs.append((False, 0, 0, opts.remote_memory, opts.cdf, 0))
#    confs.append((True, 5, 40, opts.remote_memory, opts.cdf, 0))
#    confs.append((True, -1, -1, opts.remote_memory, opts.cdf, 0))
  else:
    confs.append((opts.inject, opts.latency, opts.bandwidth, opts.remote_memory, opts.cdf, 0, opts.no_sit, opts.spark_mem))
 
  results = {}
  for conf in confs:
    results[conf] = []

  for i in range(0, opts.iter):
    for conf in confs:
      print "Running iter %d, conf %s" % (i, str(conf))
      time = run_exp(opts.task, conf[3], conf[2], conf[1], conf[5], conf[0], opts.trace, conf[4], opts.profile_io, opts.dstat, conf[6], conf[7]).get()
      results[conf].append(time)


  log("\n\n\n")
  log("================== Started exp at:%s ==================" % str(datetime.datetime.now()))
  log('Argument %s' % str(sys.argv))

  for conf in sorted(results.keys()):
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

def install_timely():
  cmd = "wget https://static.rust-lang.org/rustup.sh; sh rustup.sh -y; rm rustup.sh"
  slaves_run(cmd, tt = True)
  run(cmd)
  run("cd /root; git clone https://github.com/frankmcsherry/pagerank.git; /root/spark-ec2/copy-dir /root/pagerank")
  compile_cmd = "cd /root/pagerank; cargo build --release --bin pagerank" 
  slaves_run_parallel(compile_cmd, master = True)

def install_dstat():
  all_run("yum install -y dstat")

def install_bwmng():
  all_run("yum install -y bwm-ng --enablerepo=epel")

def install_mvn():
  cmd = '''wget http://repos.fedorapeople.org/repos/dchen/apache-maven/epel-apache-maven.repo -O /etc/yum.repos.d/epel-apache-maven.repo
sed -i s/\$releasever/6/g /etc/yum.repos.d/epel-apache-maven.repo
yum install -y apache-maven'''.replace("\n", ";")
  slaves_run_parallel(cmd, master = True)


def timely_prepare():
  cmd = "rm -rf /mnt2/timely; mkdir -p /mnt2/timely; /root/spark-ec2/copy-dir /root/s3cmd; /root/spark-ec2/copy-dir /root/.s3cfg;"
  slaves_run_parallel(cmd, master = True)

  slaves_run("rm -rf /mnt2/friendster; mkdir -p /mnt2/friendster")
  def get_offsets(server = ""):
    for i in "abcd":
      down_cmd = "~/s3cmd/s3cmd get s3://petergao/graph/friendster/friendster.offset_a%s /mnt2/friendster/friendster.offset_a%s" % (i, i)
      if server == "":
        run(down_cmd)
      else:
        run("ssh %s \"%s\"" % (server, down_cmd))
    merge_cmd = "cat /mnt2/friendster/friendster.offset* > /mnt2/timely/my-graph.offsets"
    if server == "":
      run(merge_cmd)
    else:
      run("ssh %s \"%s\"" % (server, merge_cmd))
      
  def get_targets(server = ""):
    for i in "abc":
      down_cmd = "~/s3cmd/s3cmd get s3://petergao/graph/friendster/friendster.target_a%s /mnt2/friendster/friendster.target_a%s" % (i, i)
      if server == "":
        run(down_cmd)
      else:
        run("ssh %s \"%s\"" % (server, down_cmd))
    merge_cmd = "cat /mnt2/friendster/friendster.target* > /mnt2/timely/my-graph.targets"
    if server == "":
      run(merge_cmd)
    else:
      run("ssh %s \"%s\"" % (server, merge_cmd))

  threads = [ threading.Thread(target=get_offsets, args=(s,)) for s in get_slaves()] 
  threads += [ threading.Thread(target=get_targets, args=(s,)) for s in get_slaves()] 
  [t.start() for t in threads]
  [t.join() for t in threads]

  slaves_run("rm -rf /mnt2/friendster")
  

  hosts_file = open("/mnt2/timely/hosts.txt","w")
  for s in get_slaves():
    for i in range(0,1):
      hosts_file.write(s + ":1988" + str(i) + "\n")
  hosts_file.close()
  run("/root/spark-ec2/copy-dir /mnt2/timely/hosts.txt")


def timely_run():
  global bash_run_counter
  def ssh(machine, cmd, counter):
    command = "ssh " + machine + " '" + cmd + "' &> /mnt/local_commands/cmd_" + str(counter) + ".log"
    print "#######Running cmd:" + command
    os.system(command)
    print "#######Server " + machine + " command finished"

  if not os.path.exists("/mnt/local_commands"):
    os.system("mkdir -p /mnt/local_commands")

  threads = []
  count = 0
  with open("/mnt2/timely/hosts.txt") as hosts_file:
    hosts = hosts_file.readlines()
  for line in hosts:
    s = line.split(":")[0]
    cmd = "cd /root/pagerank; cargo run --release --bin pagerank -- /mnt2/timely/my-graph -h /mnt2/timely/hosts.txt -n %s -p %s -w 6" % (len(hosts), count)
    threads.append(threading.Thread(target=ssh, args=(s, cmd, bash_run_counter,)))
    bash_run_counter += 1
    count += 1

  [t.start() for t in threads]
  [t.join() for t in threads]
  print "Finished parallel run: " + cmd

def install_all():
  update_kernel()
  slaves_run("mkdir -p /root/disaggregation/rmem/.remote_commands")
  install_blktrace()
  graphlab_install()
  memcached_install()
  install_elasticsearch()
  storm_install()
  install_mosh()
  install_s3cmd()
  install_timely()
  install_dstat()
  install_bwmng()

def prepare_env():
  stop_tachyon()
  turn_off_os_swap()
  sync_rmem_code()
  update_hadoop_conf()
  mkfs_xvdc_ext4()
  run("mkdir -p /mnt/local_commands")
  reconfig_hdfs()
  run("echo 1 > /mnt/env_prepared")

def clear_all_data():
  run("/root/ephemeral-hdfs/bin/hadoop dfs -rmr \"/*\"") #spark and hadoop
  all_run("rm -rf /mnt2/netflix_mm; rm -rf /mnt2/netflix_m") #graphlab
  all_run("rm -rf /mnt2/timely") #timely


def check_env():
  if not os.path.exists("/mnt/env_prepared"):
    print "You haven't run prepare_env. Run it now? (y/n/N)"
    input = sys.stdin.readline().strip()
    if input == "y":
      prepare_env()
    elif input == "N":
      run("echo 2 > /mnt/env_prepared")
 
 

def reconfig_hdfs_tachyon():
  print "Have you attach a 1500G+ disk (/dev/xvdf) on slave? (y/n)"
  if sys.stdin.readline().strip() != "y":
    return

  all_run("swapoff -a")
  run("/root/tachyon/bin/tachyon-stop.sh")
  run("/root/ephemeral-hdfs/bin/stop-all.sh")
  update_hdfs_conf(new_temp = "/mnt/ephemeral-hdfs", new_rep = 1, new_data = "/mnt/ephemeral-hdfs/data")
  slaves_run("umount /mnt/ramdisk; umount /mnt; rm -rf /mnt; mkdir /mnt; mount /dev/xvdf /mnt")
  
  
  run("/root/spark-ec2/copy-dir /root/ephemeral-hdfs/conf")
  run("/root/ephemeral-hdfs/bin/hadoop namenode -format -y")
  run("/root/ephemeral-hdfs/bin/start-dfs.sh")
  run("/root/tachyon/bin/tachyon-start.sh all Mount")
  run("/root/ephemeral-hdfs/bin/hadoop dfsadmin -safemode leave") 


def tachyon_prepare():
  #all_run("swapoff -a")
  #reconfig_hdfs_tachyon()
  for sz in [32]:
    terasort_spark_prepare(sz, "sparksort_input_%s" % sz)


def tachyon_run():
  sz = 32
  master = get_master()
  tachyon = True
  if tachyon:
    run("/root/spark/bin/spark-submit --class \"TeraSort\" --master \"spark://%s:7077\" --conf \"spark.executor.memory=64g\" \"/root/disaggregation/apps/spark_terasort/target/scala-2.10/terasort_2.10-1.0.jar\" \"tachyon://%s:19998/sparksort_input_%s/\" \"tachyon://%s:19998/sparksort_ouput/\"" % (master, master, sz, master) )
  else:
    run("/root/spark/bin/spark-submit --class \"TeraSort\" --master \"spark://%s:7077\" --conf \"spark.executor.memory=64g\" \"/root/disaggregation/apps/spark_terasort/target/scala-2.10/terasort_2.10-1.0.jar\" \"/sparksort_input_%s/\" \"/sparksort_ouput/\"" % (master, sz) )


def main():
  global opts
  opts = parse_args()
  run_exp_tasks = ["wordcount", "bdb", "wordcount-hadoop", "terasort", "terasort-spark", "graphlab", "memcached", "memcached-local", "storm", "timely", "elasticsearch"]
 
  if opts.task != "prepare-env":
    check_env()

  if opts.disk_vary_size:
    disk_vary_size(opts) 
  elif opts.task in run_exp_tasks:
    execute(opts)
  elif opts.task == "terasort-vary-size":
    terasort_vary_size(opts)
  elif opts.task == "terasort-prepare":
    teragen(opts.teragen_size)
  elif opts.task == "terasort-spark-prepare":
    terasort_spark_prepare(opts.teragen_size)
  elif opts.task == "wordcount-hadoop-prepare":
    wordcount_prepare()
  elif opts.task == "prepare-all":
    prepare_all(opts)

  elif opts.task == "init-rmem":
    setup_rmem(5, 40, 10, 0, True, False, "wordcount", opts.task)
  elif opts.task == "exit-rmem":
    clean_existing_rmem(40) 

  elif opts.task == "test":
    update_hdfs_conf()
  else:
    globals()[opts.task.replace("-","_")]()

if __name__ == "__main__":
  main()
