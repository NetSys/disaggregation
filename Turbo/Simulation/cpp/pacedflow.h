#ifndef PACED_FLOW_H
#define PACED_FLOW_H

#include "flow.h"
#include <iostream>
#include <assert.h>
#include <list>
#include <set>
#include <limits>

class Packet;
class Probe;
class RetxTimeoutEvent;
class FlowProcessingEvent;


class PacedFlow : public Flow {
public:
  PacedFlow(uint32_t id, double start_time, uint32_t size,
    Host *s, Host *d, double rate);
  virtual void send_pending_data();
  virtual void receive_ack(uint32_t ack);
  virtual void handle_timeout();

  double rate; // as a fraction of NIC queue capacity
};

class FullBlastPacedFlow : public PacedFlow {
public:
  FullBlastPacedFlow(uint32_t id, double start_time, uint32_t size,
    Host *s, Host *d);
};


class JitteredPacedFlow : public PacedFlow {
public:
  JitteredPacedFlow(uint32_t id, double start_time, uint32_t size,
    Host *s, Host *d, double rate);
  virtual void send_pending_data();
};

#endif
