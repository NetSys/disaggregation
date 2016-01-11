import os
import commands
import threading

bash_run_counter = 0

def banner(content):
  print "+++++++++++++++++++ " + content + " +++++++++++++++++++"

def run(cmd):
  print "###Running local cmd:" + cmd
  os.system("source ~/.bash_profile; %s" % cmd)

def run_and_get(cmd):
  return commands.getstatusoutput(cmd)

def get_master():
  with open('/root/spark-ec2/masters', 'r') as content_file:
      master = content_file.read().replace("\n","")
  return master

def log(msg, level = 0):
  f = open("/root/disaggregation/rmem/execute.py.log%s" % ("" if level == 0 else str(level)), "a")
  f.write(msg + "\n")
  f.close()

def get_slaves():
  return [line.rstrip('\n') for line in open('/root/spark-ec2/slaves')]

def scp_from(remote_file, local_file, remote_machine):
  scp_cmd = "scp -q %s:%s %s" % (remote_machine, remote_file, local_file)
  os.system(scp_cmd)

def scp_to(local_file, remote_file, remote_machine):
  scp_cmd = "scp -q %s %s:%s" % (local_file, remote_machine, remote_file)
  os.system(scp_cmd)

def slaves_run(cmd, background = False, tt = False):
  lines = get_slaves()
  for s in lines:
    command = "ssh " + ("-tt " if tt else "") + s + " \"" + cmd + "\"" + (" &> /dev/null &" if background else "")
    print "#####Running cmd:" + command
    os.system(command)

def slaves_run_parallel(cmd, master=False):
  global bash_run_counter
  def ssh(machine, cmd, counter):
    command = "ssh " + machine + " '" + cmd + "' &> /mnt/local_commands/cmd_" + str(counter) + ".log"
    print "#######Running cmd:" + command
    os.system(command)
    print "#######Server " + machine + " command finished"

  def local_run(cmd, counter):
    command = cmd 
    print "#######Running cmd:" + command
    os.system(command)
    print "#######Local cmd finished"


  if not os.path.exists("/mnt/local_commands"):
    os.system("mkdir -p /mnt/local_commands")

  threads = []
  for s in get_slaves():
    threads.append(threading.Thread(target=ssh, args=(s, cmd, bash_run_counter,)))
    bash_run_counter += 1

  if master:
    threads.append(threading.Thread(target=local_run, args=(cmd, bash_run_counter,)))
    bash_run_counter += 1

  [t.start() for t in threads]
  [t.join() for t in threads]
  print "Finished parallel run: " + cmd


def all_run(cmd, background = False):
  slaves_run(cmd, background)
  run(cmd)

def slaves_run_bash(cmd, silent = False, background = False):
  global bash_run_counter
  f = open("/root/disaggregation/rmem/.cmd_temp.sh", "w")
  f.write(cmd)
  f.close()

  print "#####Writing command to file"
  print cmd

  lines = get_slaves()
  for s in lines:
    scp_to("/root/disaggregation/rmem/.cmd_temp.sh", "/root/disaggregation/rmem/.remote_commands/cmd_%d.sh" % bash_run_counter, s)

    command = "ssh %s \"sh /root/disaggregation/rmem/.remote_commands/cmd_%d.sh%s%s\"" % (s, bash_run_counter, (" > /root/disaggregation/rmem/.remote_commands/cmd_" + str(bash_run_counter) + ".log 2>&1") if silent else "", " &" if background else "")
    print "#####Running cmd:" + command
    os.system(command)

    bash_run_counter += 1

def get_remaining_memory(machine):
  freemem = int(run_and_get("ssh %s \"cat /proc/meminfo | grep MemFree\"" % machine)[1].replace("MemFree:","").replace("kB","").replace("\n","").replace(" ",""))
  freeswap = int(run_and_get("ssh %s \"cat /proc/meminfo | grep SwapFree\"" % machine)[1].replace("SwapFree:","").replace("kB","").replace("\n","").replace(" ",""))
  return (freemem + freeswap)/1024.0/1024.0


def get_cluster_remaining_memory():
  sum = 0
  for s in get_slaves():
    mem = get_remaining_memory(s)
    sum += mem
  return sum
