#include <assert.h>

#include "schedulinghost.h"
#include "event.h"
#include "flow.h"
#include "packet.h"

extern double get_current_time();
extern void add_to_event_queue(Event*);

bool HostFlowComparator::operator() (Flow* a, Flow* b) {
    // use FIFO ordering since all flows are same size
    return a->start_time > b->start_time;
}

SchedulingHost::SchedulingHost(uint32_t id, double rate, uint32_t queue_type) : Host(id, rate, queue_type) {
    this->host_proc_event = NULL;
}

void SchedulingHost::start(Flow* f) {
    this->sending_flows.push(f);
    if (this->host_proc_event == NULL || this->host_proc_event->time < get_current_time()) {
        this->send();
    }
    else if (this->host_proc_event->host != this) {
        assert(false);
    }
}

void SchedulingHost::send() {
    if (this->sending_flows.empty()) {
        return;
    }
    
    if (!this->queue->busy) {
        while (!this->sending_flows.empty() && (this->sending_flows.top())->finished) {
            this->sending_flows.pop();    
        }
        if (this->sending_flows.empty()) {
            return;
        }
        (this->sending_flows.top())->send_pending_data();
    }
    else {
        QueueProcessingEvent *qpe = this->queue->queue_proc_event;
        uint32_t queue_size = this->queue->bytes_in_queue;
        double td = this->queue->get_transmission_delay(queue_size);
        this->host_proc_event = new HostProcessingEvent(qpe->time + td, this);
        add_to_event_queue(this->host_proc_event);
    }
}

bool RTSComparator::operator() (RTSCTS* a, RTSCTS* b) {
    //pick the RTS that arrived first
    return a->sending_time > b->sending_time;
}

RTSCTSHost::RTSCTSHost(uint32_t id, double rate, uint32_t queue_type) : SchedulingHost(id, rate, queue_type) {
    this->active_CTS = NULL;
}

void RTSCTSHost::get_RTS(RTSCTS* rts) {
    if (rts->type != RTS_PACKET) {
        return;
    }

    rts->sending_time = get_current_time();
    this->pending_RTS.push(rts);
    
    if (this->active_CTS == NULL) {
        this->send();
    }
    else if (this->host_proc_event == NULL || this->host_proc_event->time < get_current_time()) {
        this->send();
    }
}

void RTSCTSHost::send() {
    //look at RTSes first
    if (this->active_CTS == NULL && !this->pending_RTS.empty()) {
        //pick a new CTS to send
        RTSCTS* rts = this->pending_RTS.top();
        this->pending_RTS.pop();
        //send a CTS for this flow
        Packet *cts = new RTSCTS(false, get_current_time(), rts->flow, rts->size, this, rts->src);
        add_to_event_queue(new PacketQueuingEvent(get_current_time(), cts, this->queue));
        
        this->active_CTS = (RTSCTS*) cts;

        if (this->host_proc_event == NULL || this->host_proc_event->time < get_current_time()) {
            double td = queue->get_transmission_delay(cts->size);
            this->host_proc_event = new HostProcessingEvent(get_current_time() + td, this);
            add_to_event_queue(this->host_proc_event);
        }
    }
    else {
        SchedulingHost::send();
    }
}

