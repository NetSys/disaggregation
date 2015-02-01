#ifndef SCHEDULING_HOST_H
#define SCHEDULING_HOST_H

#include <set>
#include <queue>
#include "node.h"
#include "packet.h"

class Flow;
class HostProcessingEvent;

class HostFlowComparator {
public:
    bool operator() (Flow* a, Flow* b);
};

class RTSComparator {
public:
    bool operator() (RTSCTS* a, RTSCTS* b);
};

class SchedulingHost : public Host {
public:
    SchedulingHost(uint32_t id, double rate, uint32_t queue_type);
    void start(Flow* f);
    virtual void send();
    std::priority_queue<Flow*, std::vector<Flow*>, HostFlowComparator> sending_flows;
    HostProcessingEvent *host_proc_event;
};

class RTSCTSHost : public SchedulingHost {
public:
    RTSCTSHost(uint32_t id, double rate, uint32_t queue_type);
    void get_RTS(RTSCTS* rts);
    virtual void send();
    std::priority_queue<RTSCTS*, std::vector<RTSCTS*>, RTSComparator> pending_RTS;
    RTSCTS* active_CTS;
};

#endif
