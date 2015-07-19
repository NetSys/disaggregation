#ifndef FASTPASS_HOST_H
#define FASTPASS_HOST_H

#include "node.h"
#include "packet.h"
#include "params.h"
#include <map>

class ArbiterProcessingEvent;
class FastpassFlow;

class FastpassHost : public Host {
public:
    FastpassHost(uint32_t id, double rate, uint32_t queue_type);
    void receive_schedule_pkt(FastpassSchedulePkt* pkt);
};



class FastpassFlowComparator
{
public:
    bool operator() (FastpassFlow* a, FastpassFlow* b);
};

class FastpassEpochSchedule
{
public:
    FastpassEpochSchedule(double s);
    FastpassFlow* get_sender();
    double start_time;
    std::map<int, FastpassFlow*> schedule;

};

class FastpassArbiter : public Host
{
public:
    FastpassArbiter(uint32_t id, double rate, uint32_t queue_type);
    void start_arbiter();
    void schedule_proc_evt(double time);
    std::map<int, FastpassFlow*> schedule_timeslot();
    void schedule_epoch();
    void receive_rts(FastpassRTS* rts);

    ArbiterProcessingEvent* arbiter_proc_evt;
    std::priority_queue<FastpassFlow*, std::vector<FastpassFlow*>, FastpassFlowComparator> sending_flows;

};

#endif
