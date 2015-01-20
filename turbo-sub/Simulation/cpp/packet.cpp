#include "packet.h"

uint32_t Packet::instance_count = 0;

Packet::Packet(double sending_time, Flow *flow, uint32_t seq_no, uint32_t pf_priority,
  uint32_t size, Host *src, Host *dst)
{
  this->sending_time = sending_time;
  this->flow = flow;
  this->seq_no = seq_no;
  this->pf_priority = pf_priority;
  this->size = size;
  this->src = src;
  this->dst = dst;

  this->type = NORMAL_PACKET;
  this->unique_id = Packet::instance_count++;
}


Ack::Ack(Flow *flow, uint32_t seq_no_acked, std::vector<uint32_t> sack_list,
  uint32_t size,
  Host* src, Host *dst)
  : Packet(0, flow, seq_no_acked, 0, size, src, dst)
{
  this->type = ACK_PACKET;
  this->sack_list = sack_list;
}

Probe::Probe(Flow *flow, uint32_t probe_priority,
             uint32_t probe_id, bool direction,
             uint32_t size,
             Host *src, Host *dst)
             : Packet (0, flow, 0, 0, size, src, dst)
{
  this->type = PROBE_PACKET;
  this->pf_priority = probe_priority;
  this->probe_id = probe_id;
  this->direction = direction;
}

RTS::RTS(Flow *flow, uint32_t size, Host *src, Host *dst) : Packet(0, flow, 0, 0, size, src, dst) {
    this->type = RTS_PACKET;
}

CTS::CTS(Flow *flow, uint32_t size, Host *src, Host *dst) : Packet(0, flow, 0, 0, size, src, dst) {
    this->type = CTS_PACKET;
}

DTS::DTS(Flow *flow, uint32_t size, Host *src, Host *dst, double wait) : Packet(0, flow, 0, 0, size, src, dst) {
    this->type = DTS_PACKET;
    this->wait_time = wait;
}
