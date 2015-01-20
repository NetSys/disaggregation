#include "flow.h"
#include "packet.h"
#include "event.h"
#include "params.h"
#include <iostream>
#include "assert.h"
#include <math.h>

extern double get_current_time(); // TODOm
extern void add_to_event_queue(Event *);
extern int get_event_queue_size();
extern DCExpParams params;
extern uint32_t num_outstanding_packets;
extern uint32_t max_outstanding_packets;
extern uint32_t duplicated_packets_received;

Flow::Flow(uint32_t id, double start_time, uint32_t size,
    Host *s, Host *d) {
  this->id = id;
  this->start_time = start_time;
  this->finish_time = 0;
  this->size = size;
  this->src = s;
  this->dst = d;

  this->next_seq_no = 0;
  this->last_unacked_seq = 0;
  this->retx_event = NULL;
  this->flow_proc_event = NULL;

  this->received_bytes = 0;
  this->recv_till = 0;
  this->max_seq_no_recv = 0;
  this->cwnd_mss = params.initial_cwnd;
  this->max_cwnd = params.max_cwnd;
  this->finished = false;

  //SACK
  this->scoreboard_sack_bytes = 0;

  this->retx_timeout = params.retx_timeout_value;
  this->mss = params.mss;
  this->hdr_size = params.hdr_size;
  this->total_pkt_sent = 0;
  this->size_in_pkt = (int)ceil((double)size/mss);

  this->pkt_drop = 0;
  this->data_pkt_drop = 0;
  this->ack_pkt_drop = 0;
  this->flow_priority = 0;
  this->useDDCTestFlowFinishedEvent = false;
}

Flow::~Flow() {
//  packets.clear();
}

void Flow::start_flow() {
  send_pending_data();
}


void Flow::send_pending_data() {
  if (received_bytes < size) {
    //std::cout << "Sending Pending Data" << std::endl;
    uint32_t seq = next_seq_no;
    uint32_t window = cwnd_mss * mss + scoreboard_sack_bytes;
    while ((seq + mss <= last_unacked_seq + window) &&
      (seq + mss <= size)) {
      // TODO Make it explicit through the SACK list
      if (received.count(seq) == 0) {
        send(seq);
      }
      next_seq_no = seq + mss;
      seq += mss;
      //std::cout << "Adding Retx Event" << std::endl;
      if (retx_event == NULL) {
        set_timeout(get_current_time() + retx_timeout);
      }
    }
  }
}


Packet *Flow::send(uint32_t seq)
{

  Packet *p = NULL;

  uint32_t priority = get_priority(seq);
  p = new Packet(get_current_time(), this, seq, \
                 priority, mss + hdr_size, \
                 src, dst);
  this->total_pkt_sent++;

//  if(this->id == 61 || this->id == 70)
//    std::cout << "Flow::send: Flow:" << this->id << "@" << (int)(get_current_time() * 1000000) << " seq:" << seq << " sz:" << size << " pri:" << priority << " ptr:" << p <<  "\n";


  add_to_event_queue(new PacketQueuingEvent(get_current_time(), p, src->queue));
  return p;
}



void Flow::send_ack(uint32_t seq, std::vector<uint32_t> sack_list) {
  Packet *p = new Ack(this, seq, sack_list, hdr_size, dst, src); //Acks are dst->src
  add_to_event_queue(new PacketQueuingEvent(get_current_time(), p, dst->queue));
}


void Flow::receive_ack(uint32_t ack, std::vector<uint32_t> sack_list) {
  this->scoreboard_sack_bytes = sack_list.size() * mss;

  // On timeouts; next_seq_no is updated to the last_unacked_seq;
  // In such cases, the ack can be greater than next_seq_no; update it
  if (next_seq_no < ack) {
    next_seq_no = ack;
  }

  // New ack!
  if (ack > last_unacked_seq) {
    // Update the last unacked seq
    last_unacked_seq = ack;

    // Adjust cwnd
    increase_cwnd();

    // Send the remaining data
    send_pending_data();

    // Update the retx timer
    if (retx_event != NULL) { // Try to move
      cancel_retx_event();
      if (last_unacked_seq < size) {
        // Move the timeout to last_unacked_seq
        double timeout = get_current_time() + retx_timeout;
        set_timeout(timeout);
      }
    }

  }

  if (ack == size && !finished) {
    finished = true;
    received.clear();
    finish_time = get_current_time();
    flow_completion_time = finish_time - start_time;
    if(this->useDDCTestFlowFinishedEvent){
      DDCTestFlowFinishedEvent *ev = new DDCTestFlowFinishedEvent(get_current_time(), this);
      add_to_event_queue(ev);
    }else{
      FlowFinishedEvent *ev = new FlowFinishedEvent(get_current_time(), this);
      add_to_event_queue(ev);
    }
  }
}


void Flow::receive(Packet *p) {
  if (finished) {
    //std::cout << get_current_time() << " flow.cpp:162 delete " << p << "\n";
    delete p;
    return;
  }


  if (p->type == ACK_PACKET) {
    Ack *a = (Ack *) p;
    receive_ack(a->seq_no, a->sack_list);
    //std::cout << get_current_time() << " flow.cpp:170 delete " << p << "\n";
    delete p;
    return;
  }

//  if(this->id == 70 || this->id == 61){
//    std::cout << "Flow::receive:flow " << this->id << " " << (int)(get_current_time() * 1000000) << " get pkt seq:" << p->seq_no << " ptr:" << p << "\n";
//  }
  //std::cout << get_current_time() << " Received " << p->seq_no << std::endl;

  if (received.count(p->seq_no) == 0) {
    received[p->seq_no] = true;
    //std::cout << get_current_time() << " Setting " << p->seq_no << std::endl;
    num_outstanding_packets -= ((p->size - hdr_size) / (mss));
    received_bytes += (p->size - hdr_size);
  } else {
    duplicated_packets_received += 1;
  }
  if (p->seq_no > max_seq_no_recv) {
    max_seq_no_recv = p->seq_no;
  }
  // Determing which ack to send
  uint32_t s = recv_till;
  bool in_sequence = true;
  std::vector<uint32_t> sack_list;
  while (s <= max_seq_no_recv) {
    if (received.count(s) > 0) {
      //printf("s %d: count:%d\n", s, received.count(s));
      if (in_sequence) {
        recv_till += mss;
      } else {
        sack_list.push_back(s);
      }
    } else {
      in_sequence = false;
    }
    s += mss;
  }

  //std::cout << get_current_time() << " flow.cpp:209 delete " << p << "\n";
  delete p;
  //std::cout << get_current_time() << " Sending ack " << recv_till << std::endl;
  send_ack(recv_till, sack_list); // Cumulative Ack
}


void Flow::set_timeout(double time) {
  if (last_unacked_seq < size) {
    RetxTimeoutEvent *ev = new RetxTimeoutEvent(time, this);
    add_to_event_queue(ev);
    retx_event = ev;
  }
}


void Flow::handle_timeout() {
  next_seq_no = last_unacked_seq;
  //Reset congestion window to 1
  cwnd_mss = 1;
  send_pending_data(); //TODO Send again
  set_timeout(get_current_time() + retx_timeout);  // TODO
  //std::cout << "timeout\n";
}


void Flow::cancel_retx_event() {
  if (retx_event) {
    retx_event->cancelled = true;
  }
  retx_event = NULL;
}


uint32_t Flow::get_priority(uint32_t seq) {
  return (size - last_unacked_seq - scoreboard_sack_bytes);
}


void Flow::increase_cwnd() {
  cwnd_mss += 1;
  if (cwnd_mss > max_cwnd) {
    cwnd_mss = max_cwnd;
  }
}



/* Implementation for pFabric Flow */

PFabricFlow::PFabricFlow(uint32_t id, double start_time, uint32_t size, Host *s, Host *d)
 : Flow(id, start_time, size, s, d) {
  //Congestion window parameters
  this->ssthresh = 100000;
  this->count_ack_additive_increase = 0;
}

void PFabricFlow::increase_cwnd() {
  if (cwnd_mss < ssthresh) { // slow start
    cwnd_mss += 1;
  } else { // additive increase
    if (++count_ack_additive_increase >= cwnd_mss) {
      count_ack_additive_increase = 0;
      cwnd_mss += 1;
    }
  }
  // Check if we exceed max_cwnd
  if (cwnd_mss > max_cwnd) {
    cwnd_mss = max_cwnd;
  }
}

void PFabricFlow::handle_timeout() {
  ssthresh = cwnd_mss / 2;
  if (ssthresh < 2) {
    ssthresh = 2;
  }
  Flow::handle_timeout();
}

PFabricFlowNoSlowStart::PFabricFlowNoSlowStart(uint32_t id, double start_time, uint32_t size, Host *s, Host *d)
  : PFabricFlow(id, start_time, size, s, d) {
}

void PFabricFlowNoSlowStart::increase_cwnd() {
  //don't do slow start, but do additive increase
  if (++count_ack_additive_increase >= cwnd_mss) {
    count_ack_additive_increase = 0;
    cwnd_mss += 1;
  }
  if (cwnd_mss > max_cwnd) {
    cwnd_mss = max_cwnd;
  }
}

void PFabricFlowNoSlowStart::handle_timeout() {
  // do the same thing as Flow::handle_timeout but don't set cwnd = 1
  next_seq_no = last_unacked_seq;
  send_pending_data(); //TODO Send again
  set_timeout(get_current_time() + retx_timeout);  // TODO
}


FountainFlow::FountainFlow(uint32_t id, double start_time, uint32_t size, Host *s, Host *d, double redundancy)
  : Flow(id, start_time, size, s, d) {
  transmission_delay = this->src->queue->get_transmission_delay(mss + hdr_size);
  received_count = 0;
  min_recv = (int)ceil(size_in_pkt * redundancy);
  bytes_acked = 0;

  goal = (int)ceil(min_recv * 1.1);
}


void FountainFlow::start_flow() {
  this->flow_priority = ddc_get_priority();
  send_pending_data();
}


void FountainFlow::send_pending_data() {
//  if(this->id == 8)
//    std::cout << get_current_time() << " flow.cpp:333 flow:" << this->id << " send seq:" << next_seq_no << "\n";
  if (!this->finished) {
    if(!src->queue->busy){


      send(next_seq_no);
      next_seq_no += mss;
      this->flow_priority = ddc_get_priority();
      total_pkt_sent++;

//    //add a round trip time before sending parity
//    if (total_pkt_sent == min_recv){
//      add_to_event_queue(new FlowProcessingEvent(get_current_time() + 0.0000112 ,this));
//      return;
//    }

      //add_to_event_queue(new FlowProcessingEvent(get_current_time() + transmission_delay ,this));


//      if(total_pkt_sent == goal){
//        goal += (int)ceil(min_recv * 0.1);
//        add_to_event_queue(new DDCTimeoutEvent(get_current_time() + 0.0000095, this));
//      }else{
        src->active_flows.push(this);
//      }
    }else{
      src->active_flows.push(this);
    }
  }
}



void FountainFlow::receive(Packet *p) {

  if (!finished) {
    if (p->type == ACK_PACKET) {
//      Ack *a = (Ack *) p;
//      if(a->seq_no == 0){//flow finished
        finished = true;
        finish_time = get_current_time();
        flow_completion_time = finish_time - start_time;
        if(this->useDDCTestFlowFinishedEvent){
          DDCTestFlowFinishedEvent *ev = new DDCTestFlowFinishedEvent(get_current_time(), this);
          add_to_event_queue(ev);
        }else{
          FlowFinishedEvent *ev = new FlowFinishedEvent(get_current_time(), this);
          add_to_event_queue(ev);
        }
//      }else{
//        bytes_acked = a->seq_no;
//      }
    }else{
      received_count++;
//      if(this->id == 70 || this->id == 61){
//        std::cout << "flow " << this->id << " " << (int)(get_current_time() * 1000000) << " get pkt seq:" << p->seq_no << "\n";
//      }
      //TODO:fix this, this causes an underflow on NumPacketOutstanding
      num_outstanding_packets -= ((p->size - hdr_size) / (mss));
      if(received_count >= min_recv && (received_count - min_recv)%7 == 0){
        send_ack(0, dummySack);
      }
//      else{
//        send_ack(received_count * mss, dummySack);
//      }
    }

  }
  //std::cout << get_current_time() << " flow.cpp:380 delete " << p << "\n";
  delete p;
  return;
}

uint32_t FountainFlow::ddc_get_priority() {
  //uint32_t priority = min_recv * mss >= next_seq_no? min_recv * mss - next_seq_no: 2147483648 - next_seq_no;
  //uint32_t priority = min_recv * mss - bytes_acked ;
  //uint32_t priority = 2147483648 + min_recv * mss - next_seq_no;
  //uint32_t priority = this->size > next_seq_no? this->size - next_seq_no:this->size;
  //uint32_t priority = next_seq_no >= this->size?2:1;
  //uint32_t priority = this->size > next_seq_no? this->size - next_seq_no:2147483648;
  //uint32_t priority = 1;
  uint32_t priority = this->size;
  return priority;
}

void FountainFlow::send_ack(uint32_t seq, std::vector<uint32_t> sack_list) {
  Packet *p = new Ack(this, seq, sack_list, hdr_size, dst, src); //Acks are dst->src
  add_to_event_queue(new DDCHostPacketQueuingEvent(get_current_time(), p, dst->queue));

}

Packet *FountainFlow::send(uint32_t seq)
{

  Packet *p = NULL;

  //uint32_t priority = this->size > seq? this->size - seq:2147483648;

  //uint32_t priority = next_seq_no >= this->size?2:1;
  uint32_t priority = 1;
  //uint32_t priority = min_recv * mss - bytes_acked;

//  if(this->id == 8 || this->id == 6)
//    std::cout << get_current_time() << " flow " << this->id << " send seq: " << seq << "\n";



  uint32_t pkt_size = mss + hdr_size;
  p = new Packet(get_current_time(), this, seq, \
                 priority, pkt_size, \
                 src, dst);


  add_to_event_queue(new DDCHostPacketQueuingEvent(get_current_time(), p, src->queue));
  return p;
}

RTSFlow::RTSFlow(uint32_t id, double start_time, uint32_t size, Host *s, Host *d, double redundancy) : FountainFlow(id, start_time, size, s, d, redundancy) {
  cancelled_until = -1;
}

void RTSFlow::start_flow() {
    Packet *p = new RTS(this, hdr_size, src, dst);
//    if(this->id == 8 || this->id == 6)
//      std::cout << get_current_time() << " sending RTS fid:" << this->id << "\n";
    add_to_event_queue(new DDCHostPacketQueuingEvent(get_current_time(), p, src->queue));
}

void RTSFlow::send_pending_data() {
    if (this->cancelled_until < get_current_time()) {
        FountainFlow::send_pending_data();
    }
    else {
        start_flow();
    }
}

void RTSFlow::receive(Packet *p) {
    if (p->type == NORMAL_PACKET || p->type == ACK_PACKET || p->type == PROBE_PACKET) {
//        if(this->id == 8 || this->id == 6)
//          std::cout << get_current_time() << " RTSFlow::receive(Packet *p) fid:" << this->id << " recv pkt id:" << p->unique_id << " type:" << p->type << " seq:" << p->seq_no << "\n";
        FountainFlow::receive(p);
    }
    else if (p->type == RTS_PACKET) {
        if (p->dst->receiving == NULL) {
            p->dst->receiving = this;
            //send a CTS
//            if(this->id == 8 || this->id == 6)
//              std::cout << get_current_time() << " sending CTS fid:" << this->id << "\n";
            Packet *p = new CTS(this, hdr_size, dst, src);
            add_to_event_queue(new PacketQueuingEvent(get_current_time(), p, dst->queue)); 
        }
        //if this flow is shorter, preempt.
        else if (p->dst->receiving->finished) {
            //send a CTS
            Packet *p = new CTS(this, hdr_size, dst, src);
            add_to_event_queue(new PacketQueuingEvent(get_current_time(), p, dst->queue)); 
            p->dst->receiving = this;
        }
        else if (p->dst->receiving->size > this->size) {
            Flow *old_f = p->dst->receiving;
            p->dst->receiving = this;

//            if(this->id == 8 || this->id == 6)
//              std::cout << get_current_time() << " sending DTS to " << old_f->id <<  " preempting\n";
            //send a DTS to the old one
            Packet *dts = new DTS(old_f, hdr_size, dst, old_f->src, retx_timeout);
            add_to_event_queue(new PacketQueuingEvent(get_current_time(), dts, dst->queue));
            //send a CTS
//            if(this->id == 8 || this->id == 6)
//              std::cout << get_current_time() << " sending RTS to " << this->id <<  " preempting\n";
            Packet *p = new CTS(this, hdr_size, dst, src);
            add_to_event_queue(new PacketQueuingEvent(get_current_time(), p, dst->queue)); 
        }
        else {
            //send a DTS
            //for now just wait a defined time
            //Flow *f = p->dst->receiving;
//            if(this->id == 8 || this->id == 6)
//              std::cout << get_current_time() << " sending DTS fid:" << this->id << "\n";
            Packet *p = new DTS(this, hdr_size, dst, src, retx_timeout);
            add_to_event_queue(new PacketQueuingEvent(get_current_time(), p, dst->queue));
        }
    }
    else if (p->type == CTS_PACKET) {
//        if(this->id == 8 || this->id == 6)
//          std::cout << get_current_time() << " receiving CTS fid:" << this->id <<  this->cancelled_until  << "\n";
        send_pending_data();
    }
    else if (p->type == DTS_PACKET) {
//        if(this->id == 8 || this->id == 6)
//          std::cout << get_current_time() << " receiving DTS fid:" << this->id << "\n";
        //cancel sending for now
        if (flow_proc_event != NULL) {
            flow_proc_event->cancelled = true;
            flow_proc_event = NULL;
        }
        cancelled_until = get_current_time() + ((DTS*) p)->wait_time;
        add_to_event_queue(new FlowProcessingEvent(get_current_time() + ((DTS*) p)->wait_time, this));
    }
}

