#ifndef FOUNTAIN_FLOW_H
#define FOUNTAIN_FLOW_H

#include "flow.h"
#include <assert.h>

class FountainFlow : public Flow {
public:
    FountainFlow(uint32_t id, double start_time, uint32_t size, Host *s, Host *d);
    virtual void send_pending_data();
    virtual void receive(Packet *p);
    virtual Packet* send(uint32_t seq);
    virtual void send_ack();
    uint32_t received_count;
    uint32_t goal;
};

class FountainFlowWithSchedulingHost : public FountainFlow {
public:
    FountainFlowWithSchedulingHost(uint32_t id, double start_time, uint32_t size, Host *s, Host *d);
    virtual void start_flow();
    virtual void send_pending_data();
    virtual void receive(Packet *p);
};

class FountainFlowWithPipelineSchedulingHost : public FountainFlowWithSchedulingHost {
public:
  FountainFlowWithPipelineSchedulingHost(uint32_t id, double start_time, uint32_t size, Host *s, Host *d);
  void receive(Packet *p);
  void send_pending_data();
  double ack_timeout;
  int send_count;
  bool scheduled;
};

#endif

