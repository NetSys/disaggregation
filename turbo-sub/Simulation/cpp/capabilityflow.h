#ifndef CAPABILITY_FLOW_H
#define CAPABILITY_FLOW_H

#include "fountainflow.h"



struct Capability //for extendability
{
    double timeout;
};

class CapabilityComparator{
public:
    bool operator() (Capability* a, Capability* b);
};


class CapabilityFlow : public FountainFlow {
public:
    CapabilityFlow(uint32_t id, double start_time, uint32_t size, Host *s, Host *d);
    virtual void start_flow();
    virtual void send_pending_data();
    virtual void receive(Packet *p);
    Packet* send(uint32_t seq);
    void send_capability_pkt();
    void send_rts_pkt();
    bool has_capability();
    void use_capability();
    int remaining_pkts();
    void assign_init_capability();
    void set_capability_sent_count();

    std::priority_queue<Capability*, std::vector<Capability*>, CapabilityComparator> capabilities;
    bool finished_at_receiver;
    int capability_sent_count;
    double redundancy_ctrl_timeout;
    int capability_goal;
    int remaining_pkts_at_sender;
};


#endif

