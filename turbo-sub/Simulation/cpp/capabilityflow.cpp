#include "event.h"
#include "packet.h"
#include "debug.h"
#include "params.h"
#include "capabilityhost.h"
#include "capabilityflow.h"

extern double get_current_time();
extern void add_to_event_queue(Event*);
extern DCExpParams params;


bool CapabilityComparator::operator() (Capability* a, Capability* b)
{
    return a->timeout > b->timeout;
}




CapabilityFlow::CapabilityFlow(uint32_t id, double start_time, uint32_t size, Host *s, Host *d)
    :FountainFlow(id, start_time, size, s, d)
{
    this->finished_at_receiver = false;
    this->capability_sent_count = 0;
    this->redundancy_ctrl_timeout = -1;
    this->capability_goal = this->size_in_pkt;
    this->remaining_pkts_at_sender = this->size_in_pkt;
}


void CapabilityFlow::start_flow()
{
    assign_init_capability();
    set_capability_sent_count();
    ((CapabilityHost*) this->src)->start_capability_flow(this);
}


void CapabilityFlow::send_pending_data()
{
    Packet *p = this->send(next_seq_no);
    next_seq_no += mss;
    if(debug_flow(this->id))
        std::cout << get_current_time() << " flow " << this->id << " send pkt " << this->total_pkt_sent << "\n";

    double td = src->queue->get_transmission_delay(p->size);
    assert(((SchedulingHost*) src)->host_proc_event == NULL);
    ((SchedulingHost*) src)->host_proc_event = new HostProcessingEvent(get_current_time() + td + INFINITESIMAL_TIME, (SchedulingHost*) src);
    add_to_event_queue(((SchedulingHost*) src)->host_proc_event);
}



void CapabilityFlow::receive(Packet *p)
{
    if(this->finished) {
        delete p;
        return;
    }

    if(p->type == NORMAL_PACKET)
    {
        received_count++;
        if(debug_flow(this->id))
            std::cout << get_current_time() << " flow " << this->id << " received pkt " << received_count << "\n";
        if (received_count >= goal) {
            this->finished_at_receiver = true;
            send_ack();
            if(debug_flow(this->id))
                std::cout << get_current_time() << " flow " << this->id << " send ACK \n";
        }
    }
    else if(p->type == ACK_PACKET)
    {
        if(debug_flow(this->id))
            std::cout << get_current_time() << " flow " << this->id << " received ack\n";
        add_to_event_queue(new FlowFinishedEvent(get_current_time(), this));
    }
    else if(p->type == CAPABILITY_PACKET)
    {
        Capability* c = new Capability();
        c->timeout = get_current_time() + ((CapabilityPkt*)p)->ttl;
        this->capabilities.push(c);
        this->remaining_pkts_at_sender = ((CapabilityPkt*)p)->remaining_sz;

        if(((CapabilityHost*)(this->src))->host_proc_event == NULL)
        {
            ((CapabilityHost*)(this->src))->schedule_host_proc_evt();
        }
    }
    else if(p->type == RTS_PACKET)
    {
        ((CapabilityHost*)(this->dst))->active_receiving_flows.push(this);

        if( ((CapabilityHost*)(this->dst))->capa_proc_evt &&
            ((CapabilityHost*)(this->dst))->capa_proc_evt->is_timeout_evt
          )
        {
            ((CapabilityHost*)(this->dst))->capa_proc_evt->cancelled = true;
            ((CapabilityHost*)(this->dst))->capa_proc_evt = NULL;
        }

        if(((CapabilityHost*)(this->dst))->capa_proc_evt == NULL){
            ((CapabilityHost*)(this->dst))->schedule_capa_proc_evt(0, false);
        }
    }
    delete p;
}


Packet* CapabilityFlow::send(uint32_t seq)
{
    uint32_t priority = 1;
    Packet *p = new Packet(get_current_time(), this, seq, priority, mss + hdr_size, src, dst);
    total_pkt_sent++;
    add_to_event_queue(new PacketQueuingEvent(get_current_time(), p, src->queue));
    return p;
}


void CapabilityFlow::assign_init_capability(){
    int init_capa = std::min(this->size_in_pkt, CAPABILITY_INITIAL);
    for(int i = 0; i < init_capa; i++){
        Capability* c = new Capability();
        c->timeout = get_current_time() + i * 0.0000012 + CAPABILITY_TIMEOUT;
        this->capabilities.push(c);
    }
}


void CapabilityFlow::set_capability_sent_count(){
    int init_capa = std::min(this->size_in_pkt, CAPABILITY_INITIAL);
    this->capability_sent_count = init_capa;
    if(this->capability_sent_count == this->capability_goal){
        this->redundancy_ctrl_timeout = get_current_time() + CAPABILITY_RESEND_TIMEOUT;
    }
}



void CapabilityFlow::send_capability_pkt(){
    CapabilityPkt* cp = new CapabilityPkt(this, this->dst, this->src, CAPABILITY_TIMEOUT, this->remaining_pkts());
    this->capability_sent_count++;
    add_to_event_queue(new PacketQueuingEvent(get_current_time(), cp, dst->queue));
}

void CapabilityFlow::send_rts_pkt(){
    RTS* rts = new RTS(this, this->src, this->dst, 0, 0);
    add_to_event_queue(new PacketQueuingEvent(get_current_time(), rts, src->queue));
}

bool CapabilityFlow::has_capability(){
    while(!this->capabilities.empty()){
        //expired capability
        if(this->capabilities.top()->timeout < get_current_time())
        {
            delete this->capabilities.top();
            this->capabilities.pop();
        }
        //not expired
        else
        {
            return true;
        }
    }
    return false;
}

void CapabilityFlow::use_capability(){
    assert(!this->capabilities.empty() && this->capabilities.top()->timeout >= get_current_time());
    delete this->capabilities.top();
    this->capabilities.pop();
}

int CapabilityFlow::remaining_pkts(){
    return std::max((int)0, (int)(this->size_in_pkt - this->received_count));
}
