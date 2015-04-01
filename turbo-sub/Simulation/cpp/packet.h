
#ifndef PACKET_H
#define PACKET_H

#include "flow.h"
#include "node.h"
#include <stdint.h>
// TODO: Change to Enum
#define NORMAL_PACKET 0
#define ACK_PACKET 1
#define PROBE_PACKET 2

#define RTS_PACKET 3
#define CTS_PACKET 4
#define OFFER_PACKET 5
#define DECISION_PACKET 6

class Packet {

public:
	Packet(double sending_time, Flow *flow, uint32_t seq_no, uint32_t pf_priority,
		uint32_t size, Host *src, Host *dst);

	double sending_time;
	Flow *flow;
	uint32_t seq_no;
	uint32_t pf_priority;
	uint32_t size;
	Host *src;
	Host *dst;
	uint32_t unique_id;
	static uint32_t instance_count;
	int remaining_pkts_in_batch;

	uint32_t type; // Normal or Ack packet
};

class PlainAck : public Packet {
public:
    PlainAck(Flow *flow, uint32_t seq_no_acked, uint32_t size, Host* src, Host* dst);
};

class Ack : public Packet {
public:
	Ack(Flow *flow, uint32_t seq_no_acked, std::vector<uint32_t> sack_list,
    uint32_t size,
		Host* src, Host *dst);
  uint32_t sack_bytes;
	std::vector<uint32_t> sack_list;
};


class Probe : public Packet {
public:
	Probe(Flow *flow, uint32_t probe_priority,
		uint32_t probe_id, bool direction,
		uint32_t size,
		Host* src, Host *dst);
	uint32_t probe_id;
	bool direction; //Forward (true) or acking of a probe (false)
};


class RTSCTS : public Packet {
public:
    //type: true if RTS, false if CTS
    RTSCTS(bool type, double sending_time, Flow *f, uint32_t size, Host *src, Host *dst);
};

class RTS : public Packet{
public:
  RTS(Flow *flow, Host *src, Host *dst, double delay, int iter);
  double delay;
  int iter;
};

class OfferPkt : public Packet{
public:
  OfferPkt(Flow *flow, Host *src, Host *dst, bool is_free, int iter);
  bool is_free;
  int iter;
};

class DecisionPkt : public Packet{
public:
  DecisionPkt(Flow *flow, Host *src, Host *dst, bool accept);
  bool accept;
};

class CTS : public Packet{
public:
  CTS(Flow *flow, Host *src, Host *dst);
};

#endif

