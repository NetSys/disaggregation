import sys
import os
import time

class Flow:
  size = 0
  start = ""
  src = ""
  dst = ""

  def __init__(self, src, dst, start):
    self.src = src
    self.dst = dst
    self.start = start

  def __str__(self):
    return "%s %s %s %s" % (self.start, self.src, self.dst, self.size)

flows = {}

while True:
  line = sys.stdin.readline()
  #05:26:14.882269 IP ip-10-146-5-205.ec2.internal.36633 > ip-10-182-71-244.ec2.internal.etlservicemgr: Flags [.], ack 2770, win 274, options [nop,nop,TS val 6869822 ecr 6868305], length 0
  if line == "":
    break
  
  arr = line.split(" ")
  if len(arr) >= 5 and arr[1] == "IP" and arr[3] == ">" and "ec2.internal" in arr[2] and "ec2.internal" in arr[4] and "length" in arr:
    length_index = arr.index("length")
    if length_index + 1 < len(arr):
      src = arr[2]
      dst = arr[4]
      key = (src, dst)
      if key not in flows:
        flows[key] = Flow(src, dst, "%9f" % time.time())
      flows[key].size += int(arr[length_index+1])
      #print line

for f in flows.itervalues():
  print str(f)




 
