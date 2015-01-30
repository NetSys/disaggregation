#ifndef SCHEDULING_HOST_H
#define SCHEDULING_HOST_H

#include <set>
#include "node.h"

class Flow;
class HostProcessingEvent;

class HostFlowComparator {
public:
    bool operator() (Flow* a, Flow* b);
};

class SchedulingHost : public Host {
public:
    SchedulingHost(uint32_t id, double rate, uint32_t queue_type);
    void start(Flow* f);
    void send();
    std::set<Flow*, HostFlowComparator> sending_flows;
    HostProcessingEvent *host_proc_event;
};

#endif
