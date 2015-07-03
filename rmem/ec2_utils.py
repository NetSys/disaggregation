import os
import commands

def banner(content):
  print "+++++++++++++++++++ " + content + " +++++++++++++++++++"

def run(cmd):
  print "###Running local cmd:" + cmd
  os.system(cmd)

def run_and_get(cmd):
  return commands.getstatusoutput(cmd)

def get_master():
  with open('/root/spark-ec2/masters', 'r') as content_file:
      master = content_file.read().replace("\n","")
  return master


def get_slaves():
  return [line.rstrip('\n') for line in open('/root/spark-ec2/slaves')]

def scp_from(remote_file, local_file, remote_machine):
  scp_cmd = "scp -q %s:%s %s" % (remote_machine, remote_file, local_file)
  os.system(scp_cmd)

def scp_to(local_file, remote_file, remote_machine):
  scp_cmd = "scp -q %s %s:%s" % (local_file, remote_machine, remote_file)
  os.system(scp_cmd)

def slaves_run(cmd):
  lines = get_slaves()
  for s in lines:
    command = "ssh " + s + " \"" + cmd + "\""
    print "#####Running cmd:" + command
    os.system(command)

bash_run_counter = 0
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

    command = "ssh %s \"sh /root/disaggregation/rmem/.remote_commands/cmd_%d.sh%s%s\"" % (s, bash_run_counter, " > /root/disaggregation/rmem/.remote_commands/cmd_" + str(bash_run_counter) + ".log 2>&1" if silent else "", " &" if background else "")
    print "#####Running cmd:" + command
    os.system(command)

    bash_run_counter += 1
