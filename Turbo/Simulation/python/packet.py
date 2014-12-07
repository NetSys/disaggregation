import sys
from event import *


class Packet:
  NormalPacket = 0
  AckPacket = 1
  """A Packet class"""
  def __init__(self, sending_time, flow, seq_no, pf_priority, size, src, dst):
    self.flow = flow #The flow to which the packet belongs
    self.seq_no = seq_no #Sequence number for the packet
    self.pf_priority = pf_priority #
    self.size = size
    self.sending_time = sending_time
    self.type = Packet.NormalPacket #Packet
    self.src = src
    self.dst = dst

  def print_packet(self):
    print "seq:", self.seq_no, "rem:", self.pf_priority, \
      str(self.flow.src.id) + "->" + str(self.flow.dst.id)


class Ack(Packet):
  """An Ack"""
  def __init__(self, flow, seq_no_acked, size, src, dst):
    Packet.__init__(self, 0, flow, seq_no_acked, 0, size, src, dst)
    self.type = Packet.AckPacket #ACK
  
