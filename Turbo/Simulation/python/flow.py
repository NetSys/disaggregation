import sys
from event import *
from packet import *

class Flow:
  retx_timeout = 0.000045 #45 us
  mss = 1460
  hdr_size = 40
  """A Flow class"""
  def __init__(self, id, start_time, size, s, d):
    self.id = id
    self.start_time = start_time
    self.finish_time = 0
    self.size = size
    self.src = s
    self.dst = d

    self.seq_no_sent = 0
    self.rem_bytes = size

    self.last_unacked_seq = 0
    self.retx_event = None #Denotes whether a retx event exists

    self.packets = {}

    # Receiver variables
    self.received = {}
    self.received_bytes = 0
    self.recv_seq_no = 0
    self.max_seq_no_recv = 0

    self.window = 12 * Flow.mss #TODO: BDP to keep the link utilized; in #packets
    self.finished = False



  def start_flow(self):
    #print get_current_time(), self.id, "Starting flow", self.rem_bytes, "flow: (" + str(self.src.id) + "," \
    #  + str(self.dst.id) + ")"
    self.send_pending_data()
    


  def send_pending_data(self):  
  # Enqueue the packet; Call another Packet event
    if self.received_bytes < self.size:
      seq = self.seq_no_sent
        # Send as much as you can
      while (seq + Flow.mss <= self.last_unacked_seq + self.window and 
             seq + Flow.mss <= self.size):
          #if self.id == 1: print get_current_time(), "Sending ", seq, 
        packet = self.send(seq)


        #if 0 in flow_schedule.flows_to_schedule[0].packets:
        #  print "\n"
        #  print get_current_time(), "13 Pending", flow_schedule.flows_to_schedule[0].packets[0].flow.id
        #  print packet.flow.id, packet.seq_no, len(flow_schedule.flows_to_schedule[0].packets), len(self.packets)
        self.packets[seq] = packet


        assert(self.packets[seq].flow.id == self.id)

        #if 0 in flow_schedule.flows_to_schedule[0].packets:
        #  print get_current_time(), "14 Pending", flow_schedule.flows_to_schedule[0].packets[0].flow.id
        #  print "\n"
        self.rem_bytes -= Flow.mss
        self.seq_no_sent = seq + Flow.mss
        seq += Flow.mss 
        #if self.id == 0:
        #print "6 First packet id", self.id, self.packets[0].flow.id
        # If no timeout exists; add a time out
        if not self.retx_event:
          self.set_timeout(get_current_time() + Flow.retx_timeout)
          #if self.id == 26:
          #  print "Setting a RetxTimeoutEvent at", self.retx_event.time, self.id, packet.seq_no
          #  sys.stdout.flush()
    
          


      
  def send(self, seq):
    #if self.id == 0:
    #  print "6First packet id", self.packets[0].flow.id
    global event_queue
    if seq in self.packets:
      p = self.packets[seq]
      p.sending_time = get_current_time()
    else:
      p = Packet(get_current_time(), self, seq, \
                self.rem_bytes, Flow.mss + Flow.hdr_size, \
                self.src, self.dst)
    #print "Creating packet", p.flow.id, self.id
    queue = self.src.queue #Host only has queue
    # Enqueu the packet instead of adding to an event queue
    queue.enque(p)
    # No event to schedule this queue
    if not queue.busy:
      add_to_event_queue(QueueProcessingEvent(get_current_time(), queue))
      queue.busy = True
    #if self.id == 26:
    #  print get_current_time(), "Send packet", "seq:", seq, "flow: (" + \
    #    str(self.src.id) + "," + str(self.dst.id) + ")", "recv:", self.recv_seq_no
    #  sys.stdout.flush()

    return p

  def send_ack(self, seq):
    global event_queue
    p = Ack(self, seq, Flow.hdr_size, self.dst, self.src) #Acks are dst -> src
    queue = self.dst.queue
    queue.enque(p)
    if not queue.busy:
      add_to_event_queue(QueueProcessingEvent(get_current_time(), queue))
      queue.busy = True


  def receive_ack(self, ack):
    #if self.id == 0:
    #  print "5First packet id", self.packets[0].flow.id
    #if self.id == 26:
    #  print get_current_time(), "Received Ack", "seq:", ack, "flow: (" + \
    #    str(self.src.id) + "," + str(self.dst.id) + ")"
    #  sys.stdout.flush()

    if ack > self.last_unacked_seq:     #New Ack
      self.last_unacked_seq = ack
      # Check if the retx timeout must be updated
      if self.retx_event:
        #if self.id == 0:
          #print get_current_time(), "Cancelling", self.retx_event.time
        self.cancel_retx_event()
        #Check if you can move the new timeout
        #if self.id == 0:
          #print get_current_time(), "Received ACK", ack, self.seq_no_sent, self.last_unacked_seq
        if self.last_unacked_seq < self.size:
          #if self.id == 0:
          #  print get_current_time(), "New Timeout", get_current_time() + Flow.retx_timeout
          self.set_timeout(get_current_time() + Flow.retx_timeout)
            #Update the retx event TODO: ecord based on sending time
      
      self.send_pending_data()

    global remaining_event_queue
    if ack == self.size and not self.finished:
      self.finished = True
      self.finish_time = get_current_time()
      #print self.id, get_current_time(), "Flow finished in ", \
      #  str((self.finish_time - self.start_time) * 1000000.0) + "us", \
      #  self.received_bytes, self.start_time, self.src.id, self.dst.id, \
      #  len(remaining_event_queue)
      sys.stdout.flush()


  #TODO: What happens when a packet is received
  def receive(self, packet):
    if packet.type == Packet.AckPacket: #ACK
      self.receive_ack(packet.seq_no)
      return
    #if self.id == 0:
    #  print "2First packet id", self.packets[0].flow.id
    
    if packet.seq_no not in self.received:
      self.received[packet.seq_no] = True
      self.received_bytes += (packet.size - Flow.hdr_size)
    

    if packet.seq_no > self.max_seq_no_recv:
      self.max_seq_no_recv = packet.seq_no


    #Determine which ack to send
    while (1):
      if self.recv_seq_no in self.received: #received until
        self.recv_seq_no += Flow.mss
      else:
        break
    #if self.id == 26:
    #  print get_current_time(), "Received packet", "seq:", packet.seq_no, "flow: (" + \
    #    str(self.src.id) + "," + str(self.dst.id) + ")", "recv:", self.recv_seq_no
    #  sys.stdout.flush()

    # TODO: Make sending ack explicit
    self.send_ack(self.recv_seq_no)

    

  #Set timeout on last unacked seq at specified time
  def set_timeout(self, time):
    ev = RetxTimeoutEvent(time, self)
    add_to_event_queue(ev)
    self.retx_event = ev
    #if self.id == 26:
    #  print get_current_time(), "Setting a RetxTimeoutEvent at", time, self.id
    #  sys.stdout.flush()
    #if self.id == 0:
    #print get_current_time(), packet.flow.id, "New Retransmission Event", (time)

  # Timeout occurs
  def handle_timeout(self):
    #if self.id == 0:
    #  print "First packet id", self.packets[0].flow.id
    #Timeout occurs
    #print get_current_time(), "Retx Event", self.last_unacked_seq
    self.send(self.last_unacked_seq)
    self.set_timeout(get_current_time() + Flow.retx_timeout)


  def cancel_retx_event(self):
    #if self.id == 0:
    #  print "4First packet id", self.packets[0].flow.id
    global remaining_event_queue
    self.retx_event.cancelled = True
    """
    for i in range(len(remaining_event_queue)):
      x = remaining_event_queue[i]
      if x.type == 5: # it is a retx event
        if x.flow.id == self.id:
          #print self.id, "Found", event_queue[i].time, "\n"
          remaining_event_queue.pop(i)
          #heapq.heapify(remaining_event_queue)
          self.retx_event = None
          break  
    """ 

