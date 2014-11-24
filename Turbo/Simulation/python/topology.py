import sys
from globals import *
import random

def create_topology():
  num_hosts = 144

  #Capacities
  c1 = 10000000000.0
  c2 = 40000000000.0
  hosts = [Host(x, c1) for x in range(num_hosts)]

  agg_switches = [AggSwitch(x, 16, c1, 4, c2) for x in range(9)] #some lower cap links; some higher
  core_switches = [CoreSwitch(x + 9, 9, c2) for x in range(4)] #al higher cap
  switches = agg_switches + core_switches

  #Connect host queues -- PERFECT
  for i in range(144):
    h = hosts[i]
    h.queue.set_src_dst(h, agg_switches[i/16])

  # For agg switches -- REMAINING
  for i in range(len(agg_switches)): #i varies from 0 to 8
    sw = agg_switches[i]
    for j in range(16):
      q = sw.queues[j]
      q.set_src_dst(sw, hosts[i * 16 + j])

    for j in range(4):
      q = sw.queues[j + 16]
      q.set_src_dst(sw, core_switches[j])

  # For core switches -- PERFECT
  for i in range(len(core_switches)): #i varies from 0 to 3
    sw = core_switches[i]
    for j in range(9): # queues of core switch
      q = sw.queues[j]
      q.set_src_dst(sw, agg_switches[j])

  return switches, hosts


# Fix this now TODO
def get_next_hop(packet, queue):
  dst = queue.dst
  if dst.type == 'Host':
    return None # Packet Arrival

  if queue.src.type == 'Host': #Check whether in the same rack
    assert(packet.src.id == queue.src.id) #Sanity Check

    #Check in the same rack
    if packet.src.id / 16 == packet.dst.id / 16:
      return queue.dst.queues[packet.dst.id % 16]

    else: #Different rack randomize
      # TODO Flow based hashing for now
      hash_port = (packet.src.id + packet.dst.id) % 3 
      return queue.dst.queues[16 + hash_port]


  if queue.src.type == 'Switch': #Must be a switch
    #If at agg level
    if queue.src.switch_type == 'Agg':
      return queue.dst.queues[packet.dst.id / 16]
    #If at core level
    if queue.src.switch_type == 'Core':
      return queue.dst.queues[packet.dst.id % 16]

  print queue.src.type
  assert(False)
  #return packet.dst
  

# Host Class
class Node:
  def __init__(self, id, type):
    self.id = id
    self.type = type

class Host(Node):
  def __init__(self, id, rate):
    Node.__init__(self, id, 'Host')
    self.queue = PFabricQueue(id, rate, 36000)

class Switch(Node):
  def __init__(self, id, switch_type):
    Node.__init__(self, id, 'Switch')
    self.switch_type = switch_type

class CoreSwitch(Switch):
  #All queues have same rate
  def __init__(self, id, nq, rate):
    Switch.__init__(self, id, 'Core')
    self.queues = [PFabricQueue(id, rate, 36000) for id in range(nq)]

class AggSwitch(Switch):
  #Different rates -- two of them
  def __init__(self, id, nq1, r1, nq2, r2):
    Switch.__init__(self, id, 'Agg')
    q1 = [PFabricQueue(id, r1, 36000) for id in range(nq1)]
    q2 = [PFabricQueue(id, r2, 36000) for id in range(nq2)]
    self.queues = q1 + q2


class Queue:
  def __init__(self, id, rate, limit_bytes):
    self.id = id
    self.rate = rate #in bps
    self.limit_bytes = limit_bytes
    self.packets = []
    self.bytes_in_queue = 0
    self.busy = False

  def set_src_dst(self, src, dst):
    self.src = src
    self.dst = dst

  def enque(self, packet):
    if self.bytes_in_queue + packet.size <= self.limit_bytes:
      self.packets.append(packet)
      self.bytes_in_queue += packet.size
    del packet

  def deque(self):
    if len(self.packets) > 0:
      return self.packets.pop(0);

  def get_transmission_delay(self, size):
    return size * 8.0 / self.rate;


#PFabric scheduling logic
#TODO Fix the queueing methods
class PFabricQueue(Queue):
  def __init__(self, id, rate, limit_bytes):
    Queue.__init__(self, id, rate, limit_bytes)


  def enque(self, packet):
    #if 0 in flow_schedule.flows_to_schedule[0].packets:
    #  print get_current_time(), "10 Enqueing", flow_schedule.flows_to_schedule[0].packets[0].flow.id
    self.packets.append(packet)
    self.bytes_in_queue += packet.size
    #if self.id == 72:
    #  print get_current_time(), self.id, self.bytes_in_queue, "Enqueing:", 
    #  packet.print_packet()
    #if 0 in flow_schedule.flows_to_schedule[0].packets:
    #    print get_current_time(), "11 Enqueing", flow_schedule.flows_to_schedule[0].packets[0].flow.id
    #if self.id == 72 and packet.flow.id == 0:
    #  print get_current_time(), "Enqueued ", packet.seq_no, self.id, [(x.seq_no, x.flow.id) for x in self.packets]

    if self.bytes_in_queue > self.limit_bytes:
      worst_srpt = 0
      worst_packet_index = 0
      for i in range(len(self.packets)):
        p = self.packets[i]
        if p.pf_priority >= worst_srpt:
          worst_srpt = p.pf_priority
          worst_packet_index = i
      worst_packet = self.packets[worst_packet_index]
      self.bytes_in_queue -= worst_packet.size
      #print get_current_time(), "Dropping!!!!!", worst_packet.flow.id, worst_packet.seq_no, "\n"
      self.packets.pop(worst_packet_index)
      
   
  def deque(self):
    if len(self.packets) > 0:
      best_srpt = sys.maxint
      best_packet = None
      for p in self.packets:
        if p.pf_priority <= best_srpt:
          best_srpt = p.pf_priority
          best_packet = p
      #Now select the earliest flow
      best_packet_index = 0

      # Non pFabric Should be improved
      for i in range(len(self.packets)):
        if self.packets[i].flow.id == best_packet.flow.id:
          best_packet_index = i
          break
      best_packet = self.packets.pop(best_packet_index)
      self.bytes_in_queue -= best_packet.size
      
      #if self.id == 72:
      #  print get_current_time(), self.id, "Dequeing out of", self.bytes_in_queue,
      #  best_packet.print_packet()
        #if best_packet.flow.id == 0:
        #  print [(x.seq_no, x.flow.id) for x in self.packets]

      return best_packet
    else:
      return None

  