#include "schedulinghost.h"
#include "event.h"
#include "flow.h"
#include "packet.h"

extern double get_current_time();
extern void add_to_event_queue(Event*);

bool HostFlowComparator::operator() (Flow* a, Flow* b) {
    // use FIFO ordering since all flows are same size
    return a->start_time < b->start_time;
}

SchedulingHost::SchedulingHost(uint32_t id, double rate, uint32_t queue_type) : Host(id, rate, queue_type) {
    this->host_proc_event = NULL;
}

void SchedulingHost::start(Flow* f) {
    this->sending_flows.insert(f);
    if (this->host_proc_event == NULL || this->host_proc_event->time < get_current_time()) {
        this->send();
    }
}

void SchedulingHost::send() {
    if (this->sending_flows.empty()) {
        return;
    }
    
//    if (id == 137) {
//    std::cout << get_current_time() << " actives: ";
//    for (auto it = sending_flows.begin(); it != sending_flows.end(); it++) {
//        std::cout << (*it)->id << " ";
//    }
//    std::cout << "; busy? " << this->queue->busy << "\n";
//    }

    
    if (!this->queue->busy) {
        auto begin = this->sending_flows.begin();
        while (!this->sending_flows.empty() && (*begin)->finished) {
            begin = this->sending_flows.erase(begin);
        }
        if (this->sending_flows.empty()) {
            this->host_proc_event = NULL;
            return;
        }
        (*begin)->send_pending_data();
    }
    else {
        QueueProcessingEvent *qpe = this->queue->queue_proc_event;
        uint32_t queue_size = this->queue->bytes_in_queue;
        double td = this->queue->get_transmission_delay(queue_size);
        this->host_proc_event = new HostProcessingEvent(qpe->time + td, this);
        add_to_event_queue(this->host_proc_event);
    }
}

