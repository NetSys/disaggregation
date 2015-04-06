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
    this->largest_cap_seq_received = -1;
    this->latest_cap_sent_time = start_time;
}


void CapabilityFlow::start_flow()
{
    if(debug_flow(this->id))
        std::cout << get_current_time() << " flow " << this->id << " starts\n";
    assign_init_capability();
    set_capability_sent_count();
    ((CapabilityHost*) this->src)->start_capability_flow(this);
}


void CapabilityFlow::send_pending_data()
{
    int capa_seq = this->use_capability();
    Packet *p = this->send(next_seq_no, capa_seq);
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
        received_bytes += (p->size - hdr_size);
        if(p->capability_seq_num_in_data > largest_cap_seq_received)
            largest_cap_seq_received = p->capability_seq_num_in_data;
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
        c->seq_num = ((CapabilityPkt*)p)->cap_seq_num;
        this->capabilities.push(c);
        this->remaining_pkts_at_sender = ((CapabilityPkt*)p)->remaining_sz;

        if(((CapabilityHost*)(this->src))->host_proc_event == NULL)
        {
            ((CapabilityHost*)(this->src))->schedule_host_proc_evt();
        }
    }
    else if(p->type == RTS_PACKET)
    {
        if(debug_flow(p->flow->id))
            std::cout << get_current_time() << " received RTS for flow " << p->flow->id << "\n";

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


Packet* CapabilityFlow::send(uint32_t seq, int capa_seq)
{
    uint32_t priority = 1;
    Packet *p = new Packet(get_current_time(), this, seq, priority, mss + hdr_size, src, dst);
    p->capability_seq_num_in_data = capa_seq;
    total_pkt_sent++;
    add_to_event_queue(new PacketQueuingEvent(get_current_time(), p, src->queue));
    return p;
}


void CapabilityFlow::assign_init_capability(){
    //sender side
    int init_capa = std::min(this->size_in_pkt, CAPABILITY_INITIAL);
    for(int i = 0; i < init_capa; i++){
        Capability* c = new Capability();
        c->timeout = get_current_time() + i * 0.0000012 + CAPABILITY_TIMEOUT;
        c->seq_num = i;
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
    CapabilityPkt* cp = new CapabilityPkt(this, this->dst, this->src, CAPABILITY_TIMEOUT, this->remaining_pkts(), this->capability_sent_count);
    this->capability_sent_count++;
    this->latest_cap_sent_time = get_current_time();
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

int CapabilityFlow::use_capability(){
    assert(!this->capabilities.empty() && this->capabilities.top()->timeout >= get_current_time());
    int seq_num = this->capabilities.top()->seq_num;
    delete this->capabilities.top();
    this->capabilities.pop();
    return seq_num;
}

Capability* CapabilityFlow::top_capability()
{
    assert(!this->capabilities.empty());
    return this->capabilities.top();
}

double CapabilityFlow::top_capability_timeout(){
    if(this->has_capability())
        return this->top_capability()->timeout;
    else
        return 999999;
}

int CapabilityFlow::remaining_pkts(){
    return std::max((int)0, (int)(this->size_in_pkt - this->received_count));
}

int CapabilityFlow::capability_gap(){
    assert(this->capability_sent_count - this->largest_cap_seq_received >= 0);
    return this->capability_sent_count - this->largest_cap_seq_received;
}

void CapabilityFlow::relax_capability_gap()
{
    assert(this->capability_sent_count - this->largest_cap_seq_received >= 0);
    this->largest_cap_seq_received = this->capability_sent_count - CAPABILITY_WINDOW + 1;
}
