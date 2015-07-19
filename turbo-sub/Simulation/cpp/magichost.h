#ifndef MAGIC_HOST_H
#define MAGIC_HOST_H

#include <set>
#include <queue>
#include "node.h"
#include "packet.h"
#include "schedulinghost.h"
#include <map>

class MagicFlow;

class MagicHostFlowComparator {
public:
    bool operator() (MagicFlow* a, MagicFlow* b);
};

class MagicFlowTimeoutComparator{
public:
  bool operator() (MagicFlow* a, MagicFlow* b);
};

class MagicHost : public SchedulingHost {
public:
    MagicHost(uint32_t id, double rate, uint32_t queue_type);
    void start(Flow* f);
    void schedule();
    void reschedule();
    void try_send();
    void send();
    Flow* flow_sending;
    MagicFlow* flow_receiving;
    //Flow* flow_receiving;
    double recv_busy_until;
    bool is_host_proc_event_a_timeout;
    //FountainFlowWithQuickSchedulingHost* next_receiving_flow;
    std::priority_queue<MagicFlow*, std::vector<MagicFlow*>, MagicHostFlowComparator> active_sending_flows;
    std::priority_queue<MagicFlow*, std::vector<MagicFlow*>, MagicFlowTimeoutComparator> sending_redundency;
    std::map<uint32_t, MagicFlow*> receiver_pending_flows;
};


#endif
