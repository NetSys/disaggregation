#include <assert.h>


#include "event.h"
#include "flow.h"
#include "packet.h"
#include "debug.h"
#include "params.h"

#include "capabilityflow.h"
#include "capabilityhost.h"


extern double get_current_time();
extern void add_to_event_queue(Event*);
extern DCExpParams params;


bool CapabilityFlowComparator::operator() (CapabilityFlow* a, CapabilityFlow* b){
    //return a->remaining_pkts_at_sender > b->remaining_pkts_at_sender;
    if(a->remaining_pkts_at_sender > b->remaining_pkts_at_sender)
        return true;
    else if(a->remaining_pkts_at_sender == b->remaining_pkts_at_sender)
        return a->start_time > b->start_time;
    else
        return false;
    //return a->latest_data_pkt_send_time > b->latest_data_pkt_send_time;
    //return a->start_time > b->start_time;
}

bool CapabilityFlowComparatorAtReceiver::operator() (CapabilityFlow* a, CapabilityFlow* b){
    //return a->size_in_pkt > b->size_in_pkt;

    if(a->remaining_pkts() > b->remaining_pkts())
        return true;
    else if (a->remaining_pkts() == b->remaining_pkts())
        return a->start_time > b->start_time; //TODO: this is cheating. but not a big problem
    else
        return false;

    //return a->latest_cap_sent_time > b->latest_cap_sent_time;
    //return a->start_time > b->start_time;
}

CapabilityHost::CapabilityHost(uint32_t id, double rate, uint32_t queue_type)
    :SchedulingHost(id, rate, queue_type)
{
    this->capa_proc_evt = NULL;
    this->hold_on = 0;
}

void CapabilityHost::start_capability_flow(CapabilityFlow* f){
    this->active_sending_flows.push(f);
    f->send_rts_pkt();
    if(f->has_capability() && ((CapabilityHost*)(f->src))->host_proc_event == NULL){
        ((CapabilityHost*)(f->src))->schedule_host_proc_evt();
    }
}

void CapabilityHost::schedule_host_proc_evt(){
    assert(this->host_proc_event == NULL);

    double qpe_time = 0;
    double td_time = 0;
    if(this->queue->busy){
        qpe_time = this->queue->queue_proc_event->time;
    }
    else{
        qpe_time = get_current_time();
    }

    uint32_t queue_size = this->queue->bytes_in_queue;
    td_time = this->queue->get_transmission_delay(queue_size);

    this->host_proc_event = new HostProcessingEvent(qpe_time + td_time + INFINITESIMAL_TIME, this);
    add_to_event_queue(this->host_proc_event);
}

void CapabilityHost::schedule_capa_proc_evt(double time, bool is_timeout)
{
    assert(this->capa_proc_evt == NULL);
    this->capa_proc_evt = new CapabilityProcessingEvent(get_current_time() + time + INFINITESIMAL_TIME, this, is_timeout);
    add_to_event_queue(this->capa_proc_evt);
}


//should only be called in HostProcessingEvent::process()
void CapabilityHost::send(){
    assert(this->host_proc_event == NULL);


    if(this->queue->busy)
    {
        schedule_host_proc_evt();
    }
    else
    {
        std::queue<CapabilityFlow*> flows_tried;
        while(!this->active_sending_flows.empty()){
            if(this->active_sending_flows.top()->finished){
                this->active_sending_flows.pop();
                continue;
            }

            CapabilityFlow* top_flow = this->active_sending_flows.top();


            if(top_flow->has_capability())
            {
                top_flow->send_pending_data();
                break;
            }
            else{
                this->active_sending_flows.pop();
                flows_tried.push(top_flow);
            }

        }

        while(!flows_tried.empty())
        {
            CapabilityFlow* f = flows_tried.front();
            flows_tried.pop();
            this->active_sending_flows.push(f);
        }

    }

}


void CapabilityHost::send_capability(){
    //if(debug_host(this->id))
    //    std::cout << get_current_time() << " CapabilityHost::send_capability() at host " << this->id << "\n";
    assert(capa_proc_evt == NULL);

    bool capability_sent = false;
    std::queue<CapabilityFlow*> flows_tried;
    double closet_timeout = 999999;

    if(this->hold_on > 0){
        hold_on--;
        capability_sent = true;
    }

    while(!this->active_receiving_flows.empty() && !capability_sent)
    {
        CapabilityFlow* f = this->active_receiving_flows.top();
        this->active_receiving_flows.pop();
        if(debug_flow(f->id))
            std::cout << get_current_time() << " pop out flow " << f->id << "\n";


        if(f->finished_at_receiver)
        {
            continue;
        }
        flows_tried.push(f);

        //not yet timed out, shouldn't send
        if(f->redundancy_ctrl_timeout > get_current_time()){
            if(f->redundancy_ctrl_timeout < closet_timeout)
            {
                closet_timeout = f->redundancy_ctrl_timeout;
            }
        }
        //ok to send
        else
        {
            //just timeout, reset timeout state
            if(f->redundancy_ctrl_timeout > 0)
            {
                f->redundancy_ctrl_timeout = -1;
                f->capability_goal += f->remaining_pkts();
            }

            if(f->capability_gap() > CAPABILITY_WINDOW)
            {
                if(get_current_time() >= f->latest_cap_sent_time + CAPABILITY_WINDOW_TIMEOUT)
                    f->relax_capability_gap();
                else{
                    if(f->latest_cap_sent_time + CAPABILITY_WINDOW_TIMEOUT < closet_timeout)
                    {
                        closet_timeout = f->latest_cap_sent_time + CAPABILITY_WINDOW_TIMEOUT;
                    }
                }

            }


            if(f->capability_gap() <= CAPABILITY_WINDOW)
            {
                f->send_capability_pkt();
                capability_sent = true;

                if(f->capability_sent_count == f->capability_goal){
                    f->redundancy_ctrl_timeout = get_current_time() + CAPABILITY_RESEND_TIMEOUT;
                }

                break;
            }


        }
    }

    while(!flows_tried.empty()){
        CapabilityFlow* tf = flows_tried.front();
        flows_tried.pop();
        this->active_receiving_flows.push(tf);
    }



    if(capability_sent)// pkt sent
    {
        this->schedule_capa_proc_evt(0.000001232, false);
    }
    else if(closet_timeout < 999999) //has unsend flow, but its within timeout
    {
        assert(closet_timeout > get_current_time());
        this->schedule_capa_proc_evt(closet_timeout - get_current_time(), true);
    }
    else{
        //do nothing, no unfinished flow
    }
}
