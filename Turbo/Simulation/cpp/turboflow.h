#ifndef TURBO_FLOW_H
#define TURBO_FLOW_H

#include "flow.h"
#include <iostream>
#include <assert.h>
#include <list>
#include <set>
#include <limits>

class TurboFlow : public PFabricFlow {
public:
  TurboFlow(uint32_t id, double start_time, uint32_t size,
    Host *s, Host *d);
  virtual void send_pending_data();
  void receive_ack(uint32_t ack);
  virtual void receive_probe(Probe *p);
  virtual void receive(Packet *p);
  virtual void handle_timeout();
  void reset_retx_timeout();
  virtual uint32_t get_priority(uint32_t seq);
  Packet *send_probe(bool direction);

  void cancel_flow_proc_event();

  double inflation_rate;
  bool in_probe_mode;
};


class TurboFlowStopOnTimeout : public TurboFlow {
public:
  TurboFlowStopOnTimeout(uint32_t id, double start_time, uint32_t size,
    Host *s, Host *d);
  virtual void send_pending_data();
};


class TurboFlowPerPacketTimeout : public TurboFlow {
public:

  TurboFlowPerPacketTimeout(uint32_t id, double start_time, uint32_t size, Host *s, Host *d);
  virtual void send_pending_data();
  virtual void receive_ack(uint32_t ack);
  virtual void receive_probe(Probe *p);
  virtual void handle_timeout();
  virtual void reset_retx_timeout();
  // virtual uint32_t get_priority(uint32_t seq);
  uint32_t select_next_packet();

  // double priority_backoff;
  std::list<Packet*> in_flight_packets;
  std::set<uint32_t> seq_nos_inflight;
};

#endif
