import sys
import copy
#import read_trace

import operator
from packet import *
from event import *
from globals import *
from topology import *
from flow import *
import math


#Format of the file is start/finish/size/fct/s/d
def read_flows_to_schedule(f):
  fl = open(f).readlines()
  flows = []
  id = 0;
  for x in fl:
    splits = x.split()
    start_time = float(splits[0])
    size = 1460 * float(splits[2]) # Convert to bytes
    s = hosts[int(splits[5])]
    d = hosts[int(splits[6])]
    flows.append(Flow(id, start_time, size, s, d))
    id += 1
  return flows

global switches, hosts
switches, hosts = create_topology()




# Main logic
# TODO: Only schedule the l flow
global flows_to_schedule
flows_to_schedule = read_flows_to_schedule("flow_0.8Load.tr")[:300]
f1 = flows_to_schedule[0]

print len(flows_to_schedule)
for fl in flows_to_schedule:
  add_to_event_queue(FlowArrivalEvent(fl.start_time, fl))

prev_time = 0
i = 0
while len(remaining_event_queue) != 0:
  ev = get_next_event()
  if ev.cancelled:
    continue
  
  if ev.time < prev_time:
    print "Prev:", prev_time
    print "Curr:", ev.time
    print "Min:", min([e.time for e in remaining_event_queue])
    sys.exit(0)
    
  prev_time = ev.time
  #print 1000000.0 * ev.time, ev.type
  process_event(ev, hosts)
  i += 1

print len(remaining_event_queue)
simulation_time = 0


  
