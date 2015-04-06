#include "packet.h"
#include "params.h"

extern DCExpParams params;
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

PlainAck::PlainAck(Flow *flow, uint32_t seq_no_acked, uint32_t size, Host* src, Host *dst)
  : Packet(0, flow, seq_no_acked, 0, size, src, dst)
{
  this->type = ACK_PACKET;
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

RTSCTS::RTSCTS(bool type, double sending_time, Flow *f, uint32_t size, Host *src, Host *dst) : Packet(sending_time, f, 0, 0, f->hdr_size, src, dst) {
    if (type) {
        this->type = RTS_PACKET;
    }
    else {
        this->type = CTS_PACKET;
    }
}




RTS::RTS(Flow *flow, Host *src, Host *dst, double delay, int iter) : Packet(0, flow, 0, 0, params.hdr_size, src, dst) {
  this->type = RTS_PACKET;
  this->delay = delay;
  this->iter = iter;
}


OfferPkt::OfferPkt(Flow *flow, Host *src, Host *dst, bool is_free, int iter) : Packet(0, flow, 0, 0, params.hdr_size, src, dst) {
  this->type = OFFER_PACKET;
  this->is_free = is_free;
  this->iter = iter;
}

DecisionPkt::DecisionPkt(Flow *flow, Host *src, Host *dst, bool accept) : Packet(0, flow, 0, 0, params.hdr_size, src, dst) {
  this->type = DECISION_PACKET;
  this->accept = accept;
}

CTS::CTS(Flow *flow, Host *src, Host *dst) : Packet(0, flow, 0, 0, params.hdr_size, src, dst) {
  this->type = CTS_PACKET;
}

CapabilityPkt::CapabilityPkt(Flow *flow, Host *src, Host *dst, double ttl, int remaining, int cap_seq_num) : Packet(0, flow, 0, 0, params.hdr_size, src, dst) {
  this->type = CAPABILITY_PACKET;
  this->ttl = ttl;
  this->remaining_sz = remaining;
  this->cap_seq_num = cap_seq_num;
}
