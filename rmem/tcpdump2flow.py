import sys
import os
import time

class Flow:
  size = 0
  start = ""
  end = ""
  src = ""
  dst = ""
  proto = ""

  def __init__(self, src, dst, start, proto):
    self.src = src
    self.dst = dst
    self.start = start
    self.proto = proto

  def __str__(self):
    return "%s %s %s %s %s %s" % (self.start, self.end, self.src, self.dst, self.size, self.proto)

flows = {}

while True:
  line = sys.stdin.readline()
  #22:43:17.320210 IP ip-10-142-244-82.ec2.internal.60001 > dhcp-44-37.EECS.Berkeley.EDU.56876: UDP, length 237
  #05:26:14.882269 IP ip-10-146-5-205.ec2.internal.36633 > ip-10-182-71-244.ec2.internal.etlservicemgr: Flags [.], ack 2770, win 274, options [nop,nop,TS val 6869822 ecr 6868305], length 0
  if line == "":
    break
  
  arr = line.split(" ")
  if len(arr) >= 5 and arr[1] == "IP" and arr[3] == ">" and "ec2.internal" in arr[2] and "ec2.internal" in arr[4] and "length" in arr:
    length_index = arr.index("length")
    if length_index + 1 < len(arr):
      src = arr[2]
      dst = arr[4].replace(":","")
      proto = "udp" if "UDP," in arr else "tcp"
      if "memcache" in src or "memcache" in dst:
        curr_time = "%9f" % time.time()
        f = Flow(src, dst, curr_time, proto)
        f.size = int(arr[length_index+1])
        f.end = curr_time
        print str(f)
      else:
        key = (src, dst, proto)
        if key not in flows:
          flows[key] = Flow(src, dst, "%9f" % time.time(), proto)
        flows[key].size += int(arr[length_index+1])
        flows[key].end = "%9f" % time.time()
        #print line

for f in flows.itervalues():
  print str(f)




 
