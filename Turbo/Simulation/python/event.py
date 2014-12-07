#import structures

import heapq
from globals import *
from topology import *




# How to process an event
def process_event(event, hosts):
  #print event.type
  #global flow_scheduleflows_to_schedule
  #print len(flow_schedule.flows_to_schedule)
#  if 0 in flow_schedule.flows_to_schedule[0].packets:
#    print get_current_time(), "9", flow_schedule.flows_to_schedule[0].packets[0].flow.id, event.type
  if event.type == 0: # FlowArr
    process_flow_arrival_event(event)
  #if event.type == 1: # FlowPr
  #  process_flow_processing_event(event)
  if event.type == 2: #PacketQ
    process_packet_queueing_event(event)
  if event.type == 3: #PacketArr
    process_packet_arrival_event(event)
  if event.type == 4: #QueuePr
    process_queue_processing_event(event, hosts)
  if event.type == 5: #RetxTimeout
    #print event.time, "\n\n HIT HIT \n\n"
    process_retx_timeout_event(event)





#FlowArrivalEvent -- time/flow
def process_flow_arrival_event(event):
  #Flows start at line rate; so schedule a packet to be transmitted
  #First packet scheduled to be queued
  event.flow.start_flow()
  




#PacketQueuingEvent -- time/packet/queue
def process_packet_queueing_event(event):
  packet = event.packet
  queue = event.queue
  #if packet.flow.id == 0 and queue.id == 10:
  #  print "\n", get_current_time(), "Queued", packet.seq_no, "\n"
  if queue.bytes_in_queue <= 0:
  # Busy part handled here
    add_to_event_queue(QueueProcessingEvent(event.time, queue))
  queue.enque(packet)






#PacketTransmissionEvent -- time/packet
def process_queue_processing_event(event, hosts):
  queue = event.queue
  #See if some packet is there
  p = queue.deque()
  if p != None:
    queue.busy = True
    # If the next hop is the destination; receive the packet
    next_hop = get_next_hop(p, queue)

    td = queue.get_transmission_delay(p.size)
    if next_hop == None:
      add_to_event_queue(PacketArrivalEvent(event.time + td + pd, p))
    else:
      queue.busy = True
      #Have to transmit the packet p
      # Determine which queue to put the packet in
      add_to_event_queue(PacketQueuingEvent(event.time + td + pd, p, next_hop))

    # Add a new queue processing event
    add_to_event_queue(QueueProcessingEvent(event.time + td, queue))
  else:
    queue.busy = False
  





# Packet finally reaches the destination
def process_packet_arrival_event(event):
  packet = event.packet
  packet.flow.receive(packet)






def process_retx_timeout_event(event):
  #if event.packet.flow.id == 0:
  #  print "HERE HERE HERE "
  event.flow.handle_timeout()

  #print len(event_queue)
  #print get_next_event().time








class Event:
  def __init__(self, type, time):
    self.type = type
    self.time = time
    self.cancelled = False
  def __cmp__(self, other):
    if self.time < other.time:
      return -1
    if self.time > other.time:
      return 1
    #Times are equal
    return cmp(self.type, other.type)

class FlowArrivalEvent(Event):
  """A flow arrival event"""
  def __init__(self, time, flow):
    Event.__init__(self, 0, time)
    self.flow = flow

class FlowProcessingEvent(Event):
  """A packet reaches its destination"""
  def __init__(self, time, flow):
    Event.__init__(self, 1, time)
    self.flow = flow

class PacketQueuingEvent(Event):
  """A packet has to start transmission"""
  def __init__(self, time, packet, queue):
    Event.__init__(self, 2, time)
    self.packet = packet
    self.queue = queue

class PacketArrivalEvent(Event):
  """A packet reaches its destination"""
  def __init__(self, time, packet):
    Event.__init__(self, 3, time)
    self.packet = packet

class QueueProcessingEvent(Event):
  """A packet has to start transmission"""
  def __init__(self, time, queue):
    Event.__init__(self, 4, time)
    self.queue = queue

class RetxTimeoutEvent(Event):
  """A packet has to be retransmitted"""
  def __init__(self, time, flow):
    Event.__init__(self, 5, time)
    self.flow = flow

    
