#ifndef RTSCTSFLOW_H
#define RTSCTSFLOW_H

#include "fountainflow.h"

#define INIT 0
#define SENT_RTS 1
#define GOT_CTS 2

class RTSCTSFlow : public FountainFlowWithSchedulingHost {
public:
    RTSCTSFlow(uint32_t id, double start_time, uint32_t size, Host* s, Host* d);
    virtual void start_flow();
    virtual void send_pending_data();
    virtual void receive(Packet *p);
    
    // one of INIT, SENT_RTS, or GOT_CTS
    uint8_t flow_mode;
};

#endif
