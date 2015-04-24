#include "event.h"
#include "packet.h"
#include "debug.h"
#include "params.h"
#include "capabilityhost.h"
#include "capabilityflow.h"
#include "math.h"

extern double get_current_time();
extern void add_to_event_queue(Event*);
extern DCExpParams params;
extern uint32_t num_outstanding_packets;

bool CapabilityComparator::operator() (Capability* a, Capability* b)
{
    return a->timeout > b->timeout;
}




CapabilityFlow::CapabilityFlow(uint32_t id, double start_time, uint32_t size, Host *s, Host *d)
    :FountainFlow(id, start_time, size, s, d)
{
    this->finished_at_receiver = false;
    this->capability_count = 0;
    this->redundancy_ctrl_timeout = -1;
    this->capability_goal = (int)(std::ceil(this->size_in_pkt * 1.00));
    this->remaining_pkts_at_sender = this->size_in_pkt;
    this->largest_cap_seq_received = -1;
    this->total_queuing_time = 0;
    this->rts_received = false;
    this->latest_cap_sent_time = start_time;
    this->latest_data_pkt_send_time = start_time;
    this->capability_packet_sent_count = 0;
}


void CapabilityFlow::start_flow()
{
    assign_init_capability();
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
        if(!rts_received)
            std::cout << get_current_time() << " flow " << this->id << " hasn't receive rts\n";
        assert(this->rts_received);
        received_count++;
        received_bytes += (p->size - hdr_size);
        if(num_outstanding_packets >= ((p->size - hdr_size) / (mss)))
            num_outstanding_packets -= ((p->size - hdr_size) / (mss));
        else
            num_outstanding_packets = 0;
        total_queuing_time += p->total_queuing_delay;
        if(p->capability_seq_num_in_data > largest_cap_seq_received)
            largest_cap_seq_received = p->capability_seq_num_in_data;
//        if(debug_flow(this->id))
//            std::cout << get_current_time() << " flow " << this->id << " received pkt " << received_count << "\n";
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

        this->rts_received = true;
        set_capability_count();
        ((CapabilityHost*)(this->dst))->hold_on += this->init_capa_size();
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
    this->latest_data_pkt_send_time = get_current_time();
    if(this->size_in_pkt > CAPABILITY_INITIAL)
        priority = 2;
    Packet *p = new Packet(get_current_time(), this, seq, priority, mss + hdr_size, src, dst);
    p->capability_seq_num_in_data = capa_seq;
    total_pkt_sent++;
    add_to_event_queue(new PacketQueuingEvent(get_current_time(), p, src->queue));
    return p;
}


void CapabilityFlow::assign_init_capability(){
    //sender side
    int init_capa = this->init_capa_size();
    for(int i = 0; i < init_capa; i++){
        Capability* c = new Capability();
        c->timeout = get_current_time() + init_capa * 0.0000012 + CAPABILITY_TIMEOUT;
        c->seq_num = i;
        this->capabilities.push(c);
    }
}


void CapabilityFlow::set_capability_count(){
    int init_capa = this->init_capa_size();
    this->capability_count = init_capa;
    if(this->capability_count == this->capability_goal){
        this->redundancy_ctrl_timeout = get_current_time() + init_capa * 0.0000012 * 2;
    }
}



void CapabilityFlow::send_capability_pkt(){
    if(debug_flow(this->id))
        std::cout << get_current_time() << " flow " << this->id << " send capa " << this->capability_count << "\n";
    CapabilityPkt* cp = new CapabilityPkt(this, this->dst, this->src, CAPABILITY_TIMEOUT, this->remaining_pkts(), this->capability_count);
    this->capability_count++;
    this->capability_packet_sent_count++;
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
    assert(this->capability_count - this->largest_cap_seq_received >= 0);
    return this->capability_count - this->largest_cap_seq_received;
}

void CapabilityFlow::relax_capability_gap()
{
    assert(this->capability_count - this->largest_cap_seq_received >= 0);
    this->largest_cap_seq_received = this->capability_count - CAPABILITY_WINDOW;
}

int CapabilityFlow::init_capa_size(){
    return this->size_in_pkt <= CAPABILITY_INITIAL?this->size_in_pkt:0;
}


