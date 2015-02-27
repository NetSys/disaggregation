#ifndef SCHEDULING_HOST_H
#define SCHEDULING_HOST_H

#include <set>
#include <queue>
#include "node.h"
#include "packet.h"
#include "fountainflow.h"

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

class FFPipelineTimeoutComparator{
public:
  bool operator() (FountainFlowWithPipelineSchedulingHost* a, FountainFlowWithPipelineSchedulingHost* b);
};

class SchedulingHost : public Host {
public:
    SchedulingHost(uint32_t id, double rate, uint32_t queue_type);
    virtual void start(Flow* f);
    virtual void send();
    std::priority_queue<Flow*, std::vector<Flow*>, HostFlowComparator> sending_flows;
    HostProcessingEvent *host_proc_event;
};

class PipelineSchedulingHost : public SchedulingHost {
public:
    PipelineSchedulingHost(uint32_t id, double rate, uint32_t queue_type);
    void start(Flow* f);
    void try_send();
    void send();
    void send_RTS();
    void handle_rts(RTS* rts, FountainFlowWithPipelineSchedulingHost* f);
    void handle_offer_pkt(OfferPkt* offer_pkt, FountainFlowWithPipelineSchedulingHost* f);
    void handle_decision_pkt(DecisionPkt*, FountainFlowWithPipelineSchedulingHost* f);
    void receiver_offer_lock(FountainFlowWithPipelineSchedulingHost* f);
    void receiver_offer_unlock();

    FountainFlowWithPipelineSchedulingHost* current_sending_flow;
    FountainFlowWithPipelineSchedulingHost* next_sending_flow;
    int sender_schedule_state; // 0: nothing is sent, 1: RTS sent,
    int sender_rts_sent_count;
    int sender_rej_received_count;
    double sender_last_rts_send_time;

    int receiver_schedule_state; // 0: nothing is received, 1: offer sent,
    int receiver_offer_time;
    FountainFlowWithPipelineSchedulingHost* receiver_offer;

    int sender_iteration;
    int receiver_iteration;
    std::priority_queue<FountainFlowWithPipelineSchedulingHost*, std::vector<FountainFlowWithPipelineSchedulingHost*>, FFPipelineTimeoutComparator> sending_redundency;
    double sender_busy_until;
    double receiver_busy_until;

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
