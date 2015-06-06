#include <assert.h>

#include "schedulinghost.h"
#include "event.h"
#include "flow.h"
#include "packet.h"
#include "debug.h"
#include "params.h"
#include "factory.h"

extern double get_current_time();
extern void add_to_event_queue(Event*);
extern DCExpParams params;

bool HostFlowComparator::operator() (Flow* a, Flow* b) {
    // use FIFO ordering since all flows are same size
    return a->start_time > b->start_time;
}



SchedulingHost::SchedulingHost(uint32_t id, double rate, uint32_t queue_type) : Host(id, rate, queue_type, SCHEDULING_HOST) {
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



bool FFPipelineTimeoutComparator::operator() (FountainFlowWithPipelineSchedulingHost* a, FountainFlowWithPipelineSchedulingHost* b) {
    // use FIFO ordering since all flows are same size
    return a->ack_timeout > b->ack_timeout;
}


#define RTS_BATCH_SIZE 30
#define RTS_TIMEOUT 0.000003
#define RTS_ADVANCE 0.0000036
#define RECEIVER_ADVANCE 0.0000035 + 0.000001


PipelineSchedulingHost::PipelineSchedulingHost(uint32_t id, double rate, uint32_t queue_type) : SchedulingHost(id, rate, queue_type) {
    this->current_sending_flow = NULL;
    this->next_sending_flow = NULL;
    this->sender_schedule_state = 0;
    this->receiver_schedule_state = 0;
    this->sender_busy_until = 0;
    this->receiver_busy_until = 0;
    this->sender_iteration = 0;
    this->receiver_iteration = 0;
    this->receiver_offer = NULL;
    this->sender_rej_received_count = 0;
    this->sender_last_rts_send_time = 0;
    this->sender_rts_sent_count = 0;
    this->host_type = PIPELINE_SCHEDULING_HOST;
}

void PipelineSchedulingHost::start(Flow* f) {
    this->sending_flows.push(f);
    try_send();
}

void PipelineSchedulingHost::try_send(){
    if(!this->host_proc_event || this->host_proc_event->time < get_current_time()){
        this->send();
    }
}


void PipelineSchedulingHost::send() {
    double host_proc_evt_time = 10000;
    if(debug_host(this->id))
        std::cout << get_current_time() << " PipelineSchedulingHost::send() at host" << this->id << "\n";
    //put a flow to sending_redundency if all data pkts are sent

    while(this->current_sending_flow && this->current_sending_flow->finished){
        this->current_sending_flow = NULL;

        if(next_sending_flow){
            if(debug_host(this->id))
                std::cout << get_current_time() << " exist next_sending_flow, setting cur_sending_flow to " << this->next_sending_flow->id << "\n";

            this->current_sending_flow = next_sending_flow;
            this->sender_busy_until = get_current_time() + 0.0000012 * this->current_sending_flow->remaining_schd_pkt;
            next_sending_flow = NULL;
        }
    }



    if(this->current_sending_flow && ((FountainFlowWithPipelineSchedulingHost*)(this->current_sending_flow))->remaining_schd_pkt == 0){


        if(((FountainFlowWithPipelineSchedulingHost*)(this->current_sending_flow))->total_pkt_sent >= this->current_sending_flow->size_in_pkt){
            ((FountainFlowWithPipelineSchedulingHost*)(this->current_sending_flow))->ack_timeout = get_current_time() + 0.0000095;
            this->sending_redundency.push((FountainFlowWithPipelineSchedulingHost*)(this->current_sending_flow));
            if(debug_host(this->id))
                std::cout << get_current_time() << " current flow " << this->current_sending_flow->id << " finished sending data pkt\n";
        }
        else{
            this->current_sending_flow->scheduled = false;
            this->sending_flows.push(this->current_sending_flow);
            if(debug_host(this->id))
                std::cout << get_current_time() << " current flow " << this->current_sending_flow->id << " finished sending in this round\n";

        }

        this->current_sending_flow = NULL;

        if(next_sending_flow){
            if(debug_host(this->id))
                std::cout << get_current_time() << " exist next_sending_flow, setting cur_sending_flow to " << this->next_sending_flow->id << "\n";

            this->current_sending_flow = next_sending_flow;
            this->sender_busy_until = get_current_time() + 0.0000012 * this->current_sending_flow->remaining_schd_pkt;
            next_sending_flow = NULL;
        }
    }




    //if queue busy, reschedule sent()
    if(this->queue->busy){
        if(this->host_proc_event == NULL){
            QueueProcessingEvent *qpe = this->queue->queue_proc_event;
            uint32_t queue_size = this->queue->bytes_in_queue;
            double td = this->queue->get_transmission_delay(queue_size);
            if(this->host_proc_event == NULL){
                this->host_proc_event = new HostProcessingEvent(qpe->time + td + 0.000000000001, this);
                add_to_event_queue(this->host_proc_event);
            }
        }
    }
    else
    {
        bool pkt_sent = false;

        if(sender_schedule_state == 1 && get_current_time() >= sender_last_rts_send_time + RTS_TIMEOUT){
            if(debug_host(this->id)) std::cout << get_current_time() << " !set sender_schedule_state = 0 at host " << this->id <<  "\n";
            sender_schedule_state = 0;
        }

        //send rts
        if(this->sender_busy_until <= get_current_time() + RTS_ADVANCE && sender_schedule_state == 0){
            if(debug_host(this->id) )
                std::cout << get_current_time() << " calling sendRTS() at " << this->id << " sender_schedule_state:" << sender_schedule_state <<
                    " sender_last_rts_send_time:" << sender_last_rts_send_time << " sender_busy_until:" << sender_busy_until <<  "\n";
            this->send_RTS();
            if(this->sender_rts_sent_count > 0){
                pkt_sent = true;
                this->sender_last_rts_send_time = get_current_time();
                this->sender_schedule_state = 1;

                double td = this->queue->get_transmission_delay(this->queue->bytes_in_queue);
                if(this->host_proc_event == NULL){
                    this->host_proc_event = new HostProcessingEvent(get_current_time() + td + 0.000000000001, this);
                    add_to_event_queue(this->host_proc_event);
                }
            }
        }

        //send redundency packets
        if(!pkt_sent && !this->sending_redundency.empty())
        {
            while(!this->sending_redundency.empty()){
                if(this->sending_redundency.top()->finished)
                    this->sending_redundency.pop();
                else{
                    //the earliest flow timeout
                    if( this->sending_redundency.top()->ack_timeout <= get_current_time() ){
                        FountainFlowWithPipelineSchedulingHost* f = this->sending_redundency.top();
                        this->sending_redundency.pop();
                        f->send_pending_data();
                        f->ack_timeout = get_current_time() + 0.0000095;
                        this->sending_redundency.push(f);
                        pkt_sent = true;
                    // the earliest flow haven't timeout
                    }else{
                        host_proc_evt_time = this->sending_redundency.top()->ack_timeout;
                    }

                    break; //should be her
                }
            }
        }

        //send normal data packet
        if (!pkt_sent && this->current_sending_flow){
            if(debug_flow(current_sending_flow->id) || debug_host(this->id))
                std::cout << get_current_time() << " send data pkt for flow id:" << current_sending_flow->id <<
                    " src:" << current_sending_flow->src->id << " dst:" << current_sending_flow->dst->id <<
                    " seq:" << current_sending_flow->next_seq_no << "\n";
            this->current_sending_flow->send_pending_data();
            pkt_sent = true;
        }
        else if(host_proc_evt_time < 10000 && this->host_proc_event == NULL){
            this->host_proc_event = new HostProcessingEvent(host_proc_evt_time + 0.000000000001, this);
            add_to_event_queue(this->host_proc_event);
        }
//        else if(!pkt_sent){
//            while(!this->sending_flows.empty()){
//                if(this->sending_flows.top()->finished)
//                    this->sending_flows.pop();
//                else{
//                    this->sending_flows.top()->send_pending_data();
//                    pkt_sent = true;
//                    break;
//                }
//            }
//        }

    }
}


void PipelineSchedulingHost::send_RTS(){
    std::queue<FountainFlowWithPipelineSchedulingHost*> rts_sent;
    sender_rts_sent_count = 0;
    FountainFlowWithPipelineSchedulingHost* f = NULL;

//    if(this->current_sending_flow && this->current_sending_flow->total_pkt_sent < this->current_sending_flow->size_in_pkt - params.reauth_limit){
//        f = this->current_sending_flow;
//        RTS* rts = new RTS(f, f->src, f->dst, RECEIVER_ADVANCE, this->sender_iteration);
//        if(debug_flow(rts->flow->id) || debug_host(this->id))
//            std::cout << get_current_time() << " send rts for flow id:" << rts->flow->id
//            << " src:" << rts->src->id << " dst:" << rts->dst->id << " iter:" << this->sender_iteration << "\n";
//        assert(f->src->queue->limit_bytes - f->src->queue->bytes_in_queue >= rts->size);
//        add_to_event_queue(new PacketQueuingEvent(get_current_time(), rts, rts->src->queue));
//        sender_rts_sent_count++;
//    }

    for(int i = 0; i < RTS_BATCH_SIZE && !sending_flows.empty(); i++)
    {
        f = (FountainFlowWithPipelineSchedulingHost*)sending_flows.top();
        sending_flows.pop();
        if(f->finished)
            continue;
        if(!f->scheduled){
            RTS* rts = new RTS(f, f->src, f->dst, RECEIVER_ADVANCE, this->sender_iteration);
            f->rts_send_count++;
            if(debug_flow(rts->flow->id) || debug_host(this->id))
                std::cout << get_current_time() << " send rts for flow id:" << rts->flow->id
                << " src:" << rts->src->id << " dst:" << rts->dst->id << " iter:" << this->sender_iteration << "\n";
            assert(f->src->queue->limit_bytes - f->src->queue->bytes_in_queue >= rts->size);
            add_to_event_queue(new PacketQueuingEvent(get_current_time(), rts, rts->src->queue));
            rts_sent.push(f); //TODO:fix this
            sender_rts_sent_count++;
        }
    }
    while(!rts_sent.empty())
    {
        FountainFlowWithPipelineSchedulingHost* f = rts_sent.front();
        rts_sent.pop();
        sending_flows.push(f);
    }
}


void PipelineSchedulingHost::handle_rts(RTS* rts, FountainFlowWithPipelineSchedulingHost* f)
{
    if(this->receiver_schedule_state == 1 && get_current_time() >= this->receiver_offer_time + 0.000009)
    {
        this->receiver_offer_unlock();
    }

    if(this->receiver_schedule_state == 0 && get_current_time() + rts->delay >= this->receiver_busy_until)
    {
        if(debug_flow(rts->flow->id)) std::cout << get_current_time() << " host " << this->id << " accepting rts of flow " << rts->flow->id << " from " << rts->src->id << "\n";

        OfferPkt* offer = new OfferPkt(f, rts->dst, rts->src, true, rts->iter);
        add_to_event_queue(new PacketQueuingEvent(get_current_time(), offer, offer->src->queue));
        this->receiver_offer_lock(f);
    }
    else
    {
        if(debug_flow(rts->flow->id)) std::cout << get_current_time() << " host " << this->id << " rejecting rts of flow " << rts->flow->id << " from " << rts->src->id << "\n";
        OfferPkt* offer = new OfferPkt(f, rts->dst, rts->src, false, rts->iter);
        add_to_event_queue(new PacketQueuingEvent(get_current_time(), offer, offer->src->queue));
    }
}


void PipelineSchedulingHost::handle_offer_pkt(OfferPkt* offer_pkt, FountainFlowWithPipelineSchedulingHost* f)
{

   if(offer_pkt->is_free){
       if(debug_host(this->id) || debug_flow(f->id))
           std::cout << get_current_time() << " host " << this->id << " got offer for flow "
           << offer_pkt->flow->id << " curr_iter:" << this->sender_iteration << " pkt_iter:" << offer_pkt->iter << "\n";
       //accept
       if(this->sender_iteration == offer_pkt->iter && (current_sending_flow == NULL || next_sending_flow == NULL)){
           f->scheduled = true;
           f->remaining_schd_pkt = std::max((int)1, std::min((int)params.reauth_limit, (int)(f->size_in_pkt - f->total_pkt_sent)));

           this->sender_schedule_state = 0;
           this->sender_iteration++;
           this->sender_rej_received_count = 0;
           this->sender_rts_sent_count = 0;

           if(current_sending_flow)
           {
               assert(this->next_sending_flow == NULL);
               this->next_sending_flow = (FountainFlowWithPipelineSchedulingHost*)offer_pkt->flow;
               this->sender_busy_until = get_current_time() + 1500*8/params.bandwidth * this->next_sending_flow->remaining_schd_pkt;
               if(debug_host(this->id))
                   std::cout << get_current_time() << " host " << this->id << " set next sending flow " <<
                       this->next_sending_flow->id << " curr_sending_flow:" << this->current_sending_flow->id << "\n";
           }
           else
           {
               if(debug_host(this->id)) std::cout << get_current_time() << " host " << this->id << " set current sending flow to " << offer_pkt->flow->id << "\n";
               this->current_sending_flow = (FountainFlowWithPipelineSchedulingHost*)offer_pkt->flow;
               this->sender_busy_until = get_current_time() + 1500*8/params.bandwidth * this->current_sending_flow->remaining_schd_pkt;
               this->try_send();
           }
       }
       //reject
       else if(this->sender_iteration < offer_pkt->iter){
           assert(false);
       }
       else{
           DecisionPkt* decision = new DecisionPkt(f, offer_pkt->src, offer_pkt->dst, false);
       }
   }else{
       if(this->sender_iteration == offer_pkt->iter){
           this->sender_rej_received_count++;

           if(sender_rej_received_count == sender_rts_sent_count){
               this->sender_iteration++;
               this->sender_rej_received_count = 0;
               this->sender_schedule_state = 0;
               if(debug_host(this->id)) std::cout << get_current_time() << " host " << this->id << " reset state\n";
               try_send();
           }
       }



   }


}


void PipelineSchedulingHost::handle_decision_pkt(DecisionPkt* decision_pkt, FountainFlowWithPipelineSchedulingHost* f)
{
    assert(decision_pkt->accept == false);
    //TODO:verify it is from the same offer
    if(this->receiver_offer == decision_pkt->flow){
        this->receiver_offer_unlock();
    }
}

void PipelineSchedulingHost::receiver_offer_lock(FountainFlowWithPipelineSchedulingHost* f)
{
    this->receiver_iteration++;
    this->receiver_schedule_state = 1;
    this->receiver_offer_time = get_current_time();
    this->receiver_offer = f;
}

void PipelineSchedulingHost::receiver_offer_unlock()
{
    this->receiver_schedule_state = 0;
    this->receiver_offer = NULL;
    this->receiver_offer_time = 0;
    this->receiver_iteration++;
}










bool RTSComparator::operator() (RTSCTS* a, RTSCTS* b) {
    //pick the RTS that arrived first
    return a->sending_time > b->sending_time;
}

RTSCTSHost::RTSCTSHost(uint32_t id, double rate, uint32_t queue_type) : SchedulingHost(id, rate, queue_type ) {
    this->active_CTS = NULL;
    this->host_type = RTSCTS_HOST;
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

