#include "rtsctsflow.h"
#include "event.h"
#include "packet.h"

extern double get_current_time();
extern double add_to_event_queue(Event*);

RTSCTSFlow::RTSCTSFlow(uint32_t id, double start_time, uint32_t size, Host* s, Host* d)
    : FountainFlowWithSchedulingHost(id, start_time, size, s, d) {
    this->flow_mode = INIT;
}

void RTSCTSFlow::start_flow() {
    //send the RTS
    Packet *rts = new RTSCTS(true, get_current_time(), this, hdr_size, src, dst);
    add_to_event_queue(new PacketQueuingEvent(get_current_time(), rts, src->queue));
    this->flow_mode = SENT_RTS;
}

void RTSCTSFlow::send_pending_data() {
    if (this->flow_mode != GOT_CTS) {
        return;
    }
    else {
        FountainFlowWithSchedulingHost::send_pending_data();
    }
}

void RTSCTSFlow::receive(Packet *p) {
    if (this->finished) {
        return;
    }

    switch(p->type) {
        case NORMAL_PACKET:
            received_count++;
            if (received_count >= goal && (received_count - goal) % 7 == 0) {
                send_ack();
                ((RTSCTSHost*) this->dst)->active_CTS = NULL;
                ((RTSCTSHost*) this->dst)->host_proc_event = new HostProcessingEvent(get_current_time(), ((RTSCTSHost*) this->dst));
                add_to_event_queue(((RTSCTSHost*) this->dst)->host_proc_event);
            }
            break;
        
        case RTS_PACKET:
            ((RTSCTSHost*) this->dst)->get_RTS((RTSCTS*) p);
            break;
        
        case CTS_PACKET:
            this->flow_mode = GOT_CTS;
            ((SchedulingHost*) this->src)->start(this);
            break;
        
        case ACK_PACKET:
            add_to_event_queue(new FlowFinishedEvent(get_current_time(), this));
            break;
        
        default:
            assert(false);
            break;
    }
}

