
#ifndef PACKET_H
#define PACKET_H

#include "flow.h"
#include "node.h"
#include <stdint.h>
// TODO: Change to Enum
#define NORMAL_PACKET 0
#define ACK_PACKET 1
#define PROBE_PACKET 2

#define RTS_PACKET 5
#define CTS_PACKET 6
#define DTS_PACKET 7

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

	uint32_t type; // Normal or Ack packet
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

#endif

