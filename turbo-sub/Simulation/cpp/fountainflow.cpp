#include "fountainflow.h"
#include "event.h"
#include "packet.h"
#include "debug.h"
#include "params.h"

extern double get_current_time();
extern void add_to_event_queue(Event*);
extern DCExpParams params;

FountainFlow::FountainFlow(uint32_t id, double start_time, uint32_t size, Host *s, Host *d) : Flow(id, start_time, size, s, d) {
    this->goal = this->size_in_pkt;
}

void FountainFlow::send_pending_data() {
    if (this->finished) {
        return;
    }
    Packet *p = send(next_seq_no);
    next_seq_no += mss;
    //need to schedule next one
    double td = src->queue->get_transmission_delay(p->size);
    flow_proc_event = new FlowProcessingEvent(get_current_time() + td, this);
    add_to_event_queue(flow_proc_event);
}

Packet* FountainFlow::send(uint32_t seq) {
    uint32_t priority = 1;
    Packet *p = new Packet(get_current_time(), this, seq, priority, mss + hdr_size, src, dst);
    total_pkt_sent++;
    add_to_event_queue(new PacketQueuingEvent(get_current_time(), p, src->queue));
    return p;
}

void FountainFlow::send_ack() {
    Packet *ack = new PlainAck(this, 0, hdr_size, dst, src);
    add_to_event_queue(new PacketQueuingEvent(get_current_time(), ack, dst->queue));
}

void FountainFlow::receive(Packet *p) {
    if (this->finished) {
        return;
    }
    if (p->type == NORMAL_PACKET) {
        received_count++;
        //only send one ack per bdp
        if (received_count >= goal && (received_count - goal) % 7 == 0) {
            send_ack();
        }
    }
    else if (p->type == ACK_PACKET) {
        if (flow_proc_event != NULL) {
            flow_proc_event->cancelled = true;
        }
        add_to_event_queue(new FlowFinishedEvent(get_current_time(), this));
    }
    else if (p->type == RTS_PACKET){

    }
}





FountainFlowWithSchedulingHost::FountainFlowWithSchedulingHost(uint32_t id, double start_time, uint32_t size, Host *s, Host *d) : FountainFlow(id, start_time, size, s, d) {
}

void FountainFlowWithSchedulingHost::start_flow() {
    ((SchedulingHost*) this->src)->start(this);
}

void FountainFlowWithSchedulingHost::send_pending_data() {
    if (this->finished) {
        ((SchedulingHost*) this->src)->send();
        return;
    }

    Packet *p = this->send(next_seq_no);
    next_seq_no += mss;

    double td = src->queue->get_transmission_delay(p->size);
    ((SchedulingHost*) src)->host_proc_event = new HostProcessingEvent(get_current_time() + td, (SchedulingHost*) src);
    add_to_event_queue(((SchedulingHost*) src)->host_proc_event);    
}

void FountainFlowWithSchedulingHost::receive(Packet *p) {
    if (this->finished) {
        return;
    }
    if (p->type == NORMAL_PACKET) {
        received_count++;

        //only send one ack per bdp
        if (received_count >= goal && (received_count - goal) % 7 == 0) {
            send_ack();
        }
    }
    else if (p->type == ACK_PACKET) {
        add_to_event_queue(new FlowFinishedEvent(get_current_time(), this));
    }
}







FountainFlowWithPipelineSchedulingHost::FountainFlowWithPipelineSchedulingHost(uint32_t id, double start_time, uint32_t size, Host *s, Host *d)
  : FountainFlowWithSchedulingHost(id, start_time, size, s, d) {
    this->ack_timeout = 0;
    this->send_count = 0;
    this->scheduled = false;
    this->first_send_time = -1;
    this->rts_send_count = 0;
}

void FountainFlowWithPipelineSchedulingHost::send_pending_data() {
    if (this->finished) {
        return;
    }

    Packet *p = this->send(next_seq_no);
    next_seq_no += mss;
    send_count++;
    if(remaining_schd_pkt > 0)
        remaining_schd_pkt--;
    p->remaining_pkts_in_batch = remaining_schd_pkt;


    if(this->first_send_time < 0)
        this->first_send_time = get_current_time();

    if(((SchedulingHost*) src)->host_proc_event == NULL){
        double td = src->queue->get_transmission_delay(p->size);
        ((SchedulingHost*) src)->host_proc_event = new HostProcessingEvent(get_current_time() + td, (SchedulingHost*) src);
        add_to_event_queue(((SchedulingHost*) src)->host_proc_event);
    }
}

void FountainFlowWithPipelineSchedulingHost::receive(Packet *p) {
    if (this->finished) {
        return;
    }
    if (p->type == NORMAL_PACKET) {
        if(debug_flow(this->id)) std::cout << get_current_time() << " flow " << this->id << " received pkt seq no " << p->seq_no << "\n";
        received_count++;
        received_bytes += (p->size - hdr_size);

        if( ((PipelineSchedulingHost*)(this->dst))->receiver_schedule_state == 1){
            assert(((PipelineSchedulingHost*)(this->dst))->receiver_offer);
            if(((PipelineSchedulingHost*)(this->dst))->receiver_offer == p->flow){
                ((PipelineSchedulingHost*)(this->dst))->receiver_offer_unlock();
                ((PipelineSchedulingHost*)(this->dst))->receiver_busy_until = get_current_time() + p->remaining_pkts_in_batch * 0.0000018;
                assert(((PipelineSchedulingHost*)(this->dst))->receiver_busy_until >= get_current_time());
            }
        }

        //only send one ack per bdp
        if (received_count >= goal && (received_count - goal) % 7 == 0) {
            send_ack();
        }
    }
    else if (p->type == ACK_PACKET) {
        add_to_event_queue(new FlowFinishedEvent(get_current_time(), this));
    }
    else if (p->type == RTS_PACKET){
        ((PipelineSchedulingHost*)(p->dst))->handle_rts((RTS*)p, (FountainFlowWithPipelineSchedulingHost*)(p->flow));
    }
    else if (p->type == OFFER_PACKET){
        ((PipelineSchedulingHost*)(p->dst))->handle_offer_pkt((OfferPkt*)p, (FountainFlowWithPipelineSchedulingHost*)(p->flow));
    }
    else if (p->type == DECISION_PACKET){
        ((PipelineSchedulingHost*)(p->dst))->handle_decision_pkt((DecisionPkt*)p, (FountainFlowWithPipelineSchedulingHost*)(p->flow));
    }
//    else if (p->type == CTS_PACKET){
//        ((PipelineSchedulingHost*)(p->dst))->handle_cts((CTS*)p, (FountainFlowWithSchedulingHost*)(p->flow));
//    }
    delete p;
}

int FountainFlowWithPipelineSchedulingHost::get_num_pkt_to_schd()
{
    return std::max((int)1, std::min((int)params.reauth_limit, (int)(this->size_in_pkt - this->total_pkt_sent)));
}
