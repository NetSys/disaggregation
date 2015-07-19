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
  int get_num_pkt_to_schd();
  double ack_timeout;
  double first_send_time;
  int send_count;
  bool scheduled;
  int remaining_schd_pkt;
  int rts_send_count;
};

#endif

