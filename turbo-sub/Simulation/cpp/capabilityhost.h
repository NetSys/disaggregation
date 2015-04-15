#ifndef CAPABILITY_HOST_H
#define CAPABILITY_HOST_H

#include <set>
#include <queue>
#include "node.h"
#include "packet.h"
#include "schedulinghost.h"

class CapabilityProcessingEvent;
class CapabilityFlow;

class CapabilityFlowComparator
{
public:
    bool operator() (CapabilityFlow* a, CapabilityFlow* b);
};

class CapabilityFlowComparatorAtReceiver
{
public:
    bool operator() (CapabilityFlow* a, CapabilityFlow* b);
};

class CapabilityHost : public SchedulingHost {
public:
    CapabilityHost(uint32_t id, double rate, uint32_t queue_type);
    void schedule_host_proc_evt();
    void start_capability_flow(CapabilityFlow* f);
    void send();
    std::priority_queue<CapabilityFlow*, std::vector<CapabilityFlow*>, CapabilityFlowComparator> active_sending_flows;

    void send_capability();
    void schedule_capa_proc_evt(double time, bool is_timeout);
    std::priority_queue<CapabilityFlow*, std::vector<CapabilityFlow*>, CapabilityFlowComparatorAtReceiver> active_receiving_flows;
    CapabilityProcessingEvent *capa_proc_evt;
    int hold_on;
};



#endif
