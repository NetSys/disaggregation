#include "turboflow.h"
#include "packet.h"
#include "event.h"

extern double get_current_time(); // TODO
extern void add_to_event_queue(Event *);
extern int get_event_queue_size();

/* Implementation for the Turbo flow */

TurboFlow::TurboFlow(uint32_t id, double start_time, uint32_t size,
  Host *s, Host *d) : PFabricFlow(id, start_time, size, s, d) {
  this->inflation_rate = 1.0;
  this->in_probe_mode = false;
}


void TurboFlow::send_pending_data() {
  // Time to send probe
  if (in_probe_mode) {
    in_probe_mode = false; // TODO temporary fix to prevent sending too many probes
    Packet *p = send_probe(true); // Probe in forward direction
    double td = src->queue->get_transmission_delay(p->size);
    flow_proc_event = new FlowProcessingEvent(get_current_time() + td, this);
    add_to_event_queue(flow_proc_event);
    if (retx_event == NULL) {
      set_timeout(get_current_time() + retx_timeout);
    }
    return;
  }

  if (received_bytes < size) {
    // Outside the end of the flow
    if (next_seq_no + mss > size) {
      flow_proc_event = NULL;
      return;
    }
    uint32_t seq_to_send = next_seq_no;
    next_seq_no += mss; // Advance the next_seq_no
    if (received.count(seq_to_send) == 0) {
      Packet *p = send(seq_to_send);
      double td = src->queue->get_transmission_delay(p->size);
      flow_proc_event = new FlowProcessingEvent(get_current_time() + td, this);
      add_to_event_queue(flow_proc_event);
      if (retx_event == NULL) {
        set_timeout(get_current_time() + retx_timeout);
      }
    } else {
      send_pending_data();
    }
  }
}


void TurboFlow::receive_ack(uint32_t ack) {

  //if (id == 1)
  //  std::cout << 1000000 * get_current_time() << " Received ack: " << ack << std::endl;
  // On timeouts; next_seq_no is updated to the last_unacked_seq;
  // In such cases, the ack can be greater than next_seq_no; update it
  if (next_seq_no < ack) {
    next_seq_no = ack;
  }

  // New ack!
  if (ack > last_unacked_seq) {
    // Update the last unacked seq
    last_unacked_seq = ack;
    inflation_rate = 1.0;
    in_probe_mode = false;
    reset_retx_timeout();
  } else { // Dup Ack
    /*if (sack_bytes > scoreboard_sack_bytes) {
      next_seq_no = last_unacked_seq;
      if (flow_proc_event == NULL) { // only if flow_proc_event is not sent
        flow_proc_event = new FlowProcessingEvent(get_current_time(), this);
        add_to_event_queue(flow_proc_event);
      }
    }*/
  }

  if (ack == size && !finished) {
    finished = true;
    received.clear();
    finish_time = get_current_time();
    flow_completion_time = finish_time - start_time;
    FlowFinishedEvent *ev = new FlowFinishedEvent(get_current_time(), this);
    add_to_event_queue(ev);
    cancel_flow_proc_event();
    cancel_retx_event();
  }
}


void TurboFlow::receive_probe(Probe *p) {
  if (finished) {
    delete p;
    return;
  }
  if (p->direction) { // Have received a probe packet should
    send_probe(false); // Send ack to
  } else { // Received reply to a probe
    // TODO: Check if the probe ids match
    inflation_rate = 1.0;
    in_probe_mode = false;
    // TODO: URGENT think about this whether to reset or not
    cancel_retx_event();

    next_seq_no = last_unacked_seq;
    if (flow_proc_event == NULL) {
      flow_proc_event = new FlowProcessingEvent(get_current_time(), this);
      add_to_event_queue(flow_proc_event);
    }
  }
}


void TurboFlow::receive(Packet *p) {
  if (finished) {
    delete p;
    return;
  }
  // Packet is an ACK
  if (p->type == ACK_PACKET) {
    receive_ack(p->seq_no);
    this->scoreboard_sack_bytes = ((Ack *) p)->sack_bytes;
    delete p;
    return;
  }
  // Packet is a probe
  if (p->type == PROBE_PACKET) {
    receive_probe((Probe *)p);
    delete p;
    return;
  }

  // Data Packet
  if (received.count(p->seq_no) == 0) {
    received[p->seq_no] = true;
    received_bytes += (p->size - hdr_size);
  }

  if (p->seq_no > max_seq_no_recv) {
    max_seq_no_recv = p->seq_no;
  }

  // Determing which ack to send
  uint32_t s = recv_till;
  bool in_sequence = true;
  uint32_t sack_bytes = 0;
  while (s <= max_seq_no_recv) {
    if (received.count(s) > 0) {
      //printf("s %d: count:%d\n", s, received.count(s));
      if (in_sequence) {
        recv_till += mss;
      } else {
        sack_bytes += mss;
      }
    } else {
      in_sequence = false;
    }
    s += mss;
  }
  delete p;
  send_ack(recv_till, sack_bytes); // Cumulative Ack
}

void TurboFlow::handle_timeout()
{
  // TODO don't let inflation rate get too inflated
  /*if (inflation_rate > max_inflation_rate) {
    inflation_rate = max_inflation_rate;
  }*/
  inflation_rate *= 2; //INT_MAX;
  in_probe_mode = true;
  //std::cout << 1000000 * get_current_time() << "Timeout!\n";
  next_seq_no = last_unacked_seq;
  if (flow_proc_event == NULL) {
    flow_proc_event = new FlowProcessingEvent(get_current_time(), this);
    add_to_event_queue(flow_proc_event);
  }
  // TODO: Think!!!! whether to reset it or not
  cancel_retx_event();
}

void TurboFlow::reset_retx_timeout() {
  if (retx_event) {
    retx_event->cancelled = true; // Makes sure that the event is not triggered
  }
  // TODO: Be more accurate about the time
  set_timeout(get_current_time() + retx_timeout);
}


void TurboFlow::cancel_flow_proc_event() {
  if (flow_proc_event) {
    flow_proc_event->cancelled = true;
  }
  flow_proc_event = NULL;
}


uint32_t TurboFlow::get_priority(uint32_t seq) {
  uint32_t real_priority = Flow::get_priority(seq);
//  uint32_t real_priority = size;

  return real_priority * inflation_rate;
}


Packet* TurboFlow::send_probe(bool direction) {
  uint32_t priority = 0;
  Probe *p;
  if (direction) {
    // Probes go at real priority
    priority = get_priority(next_seq_no) / this->inflation_rate;
    p = new Probe(this, priority, 0, direction, hdr_size, src, dst);
    add_to_event_queue(new PacketQueuingEvent(get_current_time(), p, src->queue));
  } else {
    // Probe Ack
    p = new Probe(this, priority, 0, direction, hdr_size, dst, src);
    add_to_event_queue(new PacketQueuingEvent(get_current_time(), p, dst->queue));
  }
  // TODO set proper probe id
  return p;
}




/* Implementation for the Turbo Flow that stops on timeout */

TurboFlowStopOnTimeout::TurboFlowStopOnTimeout(
  uint32_t id, double start_time, uint32_t size,
  Host *s, Host *d) : TurboFlow(id, start_time, size, s, d) {
}

void TurboFlowStopOnTimeout::send_pending_data() {
  // Time to send probe
  if (in_probe_mode) {
    //in_probe_mode = false; // TODO temporary
    //fix to prevent sending too many probes
    send_probe(true); // Probe in forward direction
    flow_proc_event = new FlowProcessingEvent(get_current_time() +
      retx_timeout, this);
    add_to_event_queue(flow_proc_event);
    if (retx_event == NULL) {
      set_timeout(get_current_time() + retx_timeout);
    }
    return;
  }

  if (received_bytes < size) {
    // Outside the end of the flow
    if (next_seq_no + mss > size) {
      flow_proc_event = NULL;
      return;
    }
    uint32_t seq_to_send = next_seq_no;
    next_seq_no += mss; // Advance the next_seq_no
    if (received.count(seq_to_send) == 0) {
      Packet *p = send(seq_to_send);
      double td = src->queue->get_transmission_delay(p->size);
      flow_proc_event = new FlowProcessingEvent(get_current_time() + td, this);
      add_to_event_queue(flow_proc_event);
      if (retx_event == NULL) {
        set_timeout(get_current_time() + retx_timeout);
      }
    } else {
      send_pending_data();
    }
  }
}






/* Per Packet Timeout Scheme thanks to Kaifei */

TurboFlowPerPacketTimeout::TurboFlowPerPacketTimeout(
  uint32_t id, double start_time, uint32_t size,
  Host *s, Host *d) : TurboFlow(id, start_time, size, s, d) {
}

uint32_t TurboFlowPerPacketTimeout::select_next_packet() {
  /* Kaifei's Logic
    // TODO TIMEOUT send the first data packet whose seq number:
     // is not (in flight)(in send_log and flagged 0), and,
     // is not acked (indicated by some other data structured you maintained in this code)
     //
     // if there is no such seq number packet, send any one whose seq number:
     // is not acked

 */
  uint32_t seq_to_send = last_unacked_seq;
  while (seq_to_send < size) {
    // if (seq_nos_inflight.find(seq_to_send) != seq_nos_inflight.end() || (received.count(seq_to_send) != 0)) {
    //   //can't send this, its already in flight
    //   seq_to_send += mss; //go to the next packet
    //   continue;
    // }
    // //this one isn't inflight so we can send it.
    // // priority_backoff = 1;
    // return seq_to_send;
    if (received.count(seq_to_send) != 0) {
      seq_to_send += mss;
      continue;
    }
    bool done = true;
    for (std::list<Packet*>::iterator it = in_flight_packets.begin();it != in_flight_packets.end();it++) {
      if ((*it)->seq_no == seq_to_send) {
        seq_to_send += mss;
        done = false;
        break;
      }
    }
    if (!done) {
      continue;
    }
    return seq_to_send;
  }
  //we couldn't find any good packets to send. Just cycle back with priority backoff.
  // seq_to_send = last_unacked_seq;
  // //TODO 1.5 here is arbitrary
  // priority_backoff *= 1.5;

  seq_to_send = last_unacked_seq - 1; //signal to stop sending
  return seq_to_send;
}

void TurboFlowPerPacketTimeout::send_pending_data() {
  // Time to send probe
  if (in_probe_mode) {
    in_probe_mode = false; // TODO temporary fix to prevent sending too many probes
    Packet *p = send_probe(true); // Probe in forward direction
    double td = src->queue->get_transmission_delay(p->size);
    flow_proc_event = new FlowProcessingEvent(get_current_time() + td, this);
    add_to_event_queue(flow_proc_event);
    if (retx_event == NULL) {
      set_timeout(get_current_time() + retx_timeout);
    }
    return;
  }

  // Time to send data
  if (received_bytes < size) {
    //find out what packet to send
    uint32_t seq_to_send = select_next_packet();
    if (seq_to_send == last_unacked_seq-1) {
      flow_proc_event = NULL;
      return;
    }
    Packet *p = send(seq_to_send);
    this->in_flight_packets.push_back(p);
    // this->seq_nos_inflight.insert(p->seq_no);
    // if (in_flight_packets.size() != seq_nos_inflight.size()) {
    //   std::cout << "size mismatch (send)!! " << in_flight_packets.size() << " " << seq_nos_inflight.size() << std::endl;
    //   assert(false);
    // }
    double td = src->queue->get_transmission_delay(p->size);
    flow_proc_event = new FlowProcessingEvent(get_current_time() + td, this);
    add_to_event_queue(flow_proc_event);
    if (retx_event == NULL) {
      set_timeout(get_current_time() + retx_timeout);
    }
  }
}

void TurboFlowPerPacketTimeout::receive_ack(uint32_t ack) {
  /* Kaifei's Logic
   // TODO TIMEOUT flag the correspondng packet in send_log with corresponding
   //packet number (ack is corresponding to a packet number AND a seq number) as 2.
   //
   // Remove all heading 1-flagged and 2-flagged packet log in send_log.
   //
   //flag the seq number in your maintained data structure as ACKed
   //
   //if the timeout is for this packet, rescheulde another timeout whose value is
   // (sent time of first packet in send_log whose flag is 0 (should be the head)
   // + RTO)
   */


  // On timeouts; next_seq_no is updated to the last_unacked_seq;
  // In such cases, the ack can be greater than next_seq_no; update it
  if (next_seq_no < ack) {
    next_seq_no = ack;
  }

  // New ack!
  if (ack > last_unacked_seq) {
    // Update the last unacked seq
    last_unacked_seq = ack;
    // if (in_probe_mode || inflation_rate > 1.0) {
      // std::cout << 1e6*get_current_time() << " exiting pm from ack " << id << std::endl;
    // }
    inflation_rate = 1.0;
    in_probe_mode = false;

    //must remove packets from queue that have been acked since they are no longer inflight
    std::list<Packet*>::iterator p = in_flight_packets.begin();
    std::vector<std::list<Packet*>::iterator> to_delete;
    while(p != in_flight_packets.end()) {
      if ((*p)->seq_no < ack) {
        to_delete.push_back(p);
      }
      p++;
    }
    for (uint32_t i = 0; i < to_delete.size(); i++) {
      in_flight_packets.erase(to_delete[i]);
      // seq_nos_inflight.erase((*(to_delete[i]))->seq_no);
    }

    // if (in_flight_packets.size() != seq_nos_inflight.size()) {
    //   std::cout << "size mismatch (ack)!! " << in_flight_packets.size() << " " << seq_nos_inflight.size() << std::endl;
    //   assert(false);
    // }


    reset_retx_timeout();
    if (flow_proc_event == NULL) {
      flow_proc_event = new FlowProcessingEvent(get_current_time(), this);
      add_to_event_queue(flow_proc_event);
    }
  } else { // Dup Ack
    /*if (sack_bytes > scoreboard_sack_bytes) {
      next_seq_no = last_unacked_seq;
      if (flow_proc_event == NULL) { // only if flow_proc_event is not sent
        flow_proc_event = new FlowProcessingEvent(get_current_time(), this);
        add_to_event_queue(flow_proc_event);
      }
    }*/
  }

  if (ack == size && !finished) {
    finished = true;
    finish_time = get_current_time();
    flow_completion_time = finish_time - start_time;
    FlowFinishedEvent *ev = new FlowFinishedEvent(get_current_time(), this);
    add_to_event_queue(ev);
    cancel_flow_proc_event();
    cancel_retx_event();
  }
}

void TurboFlowPerPacketTimeout::receive_probe(Probe *p) {
  if (finished) {
    return;
  }
  if (p->direction) { // Have received a probe packet should
    send_probe(false); // Send ack to
  } else { // Received reply to a probe
    // TODO: Check if the probe ids match
    inflation_rate = 1.0;
    in_probe_mode = false;
    // std::cout << 1e6*get_current_time() << " exiting pm from pr_ack " << id << std::endl;
    // TODO: URGENT think about this whether to reset or not
    reset_retx_timeout();

    // next_seq_no = last_unacked_seq;
    if (flow_proc_event == NULL) {
      flow_proc_event = new FlowProcessingEvent(get_current_time(), this);
      add_to_event_queue(flow_proc_event);
    }
  }
}

void TurboFlowPerPacketTimeout::handle_timeout()
{
  /* Kaifei's logic
  // TODO TIMEOUT flag the corresponding packet (timeout should be corresponded to
   // a packet number) as 1.
   //
   // Remove all heading 1-flagged and 2-flagged packet log from send_log.
   //
   // schedule another timeout whose value is
   // (sent time of first packet in send_log whose flag is 0 (should be the head)
   // + RTO)
   */

  inflation_rate *= 2.0;
  // TODO don't let inflation rate get too inflated
  /*if (inflation_rate > max_inflation_rate) {
    inflation_rate = max_inflation_rate;
  }*/

  in_probe_mode = true;
  // std::cout << 1e6*get_current_time() << " timed out " << id << " " << inflation_rate << std::endl;

  // next_seq_no = last_unacked_seq;

  //the packet that caused the timeout is re-sent
  //when sent will be readded to the in_flight_packets
  // if (id == 8 || in_flight_packets.size() == 1 && seq_nos_inflight.size() == 1) {
  //   std::cout << in_flight_packets.size() << " " << seq_nos_inflight.size() << "\n";
  //   std::cout << "list\n";
  //   for (std::list<Packet*>::iterator it=in_flight_packets.begin(); it!=in_flight_packets.end(); ++it) std::cout << ' ' << (*it)->seq_no;
  //   std::cout << "\nset\n";
  //   for (std::set<uint32_t>::iterator it=seq_nos_inflight.begin(); it!=seq_nos_inflight.end(); ++it) std::cout << ' ' << *it;
  //   std::cout << '\n';
  // }
  if (in_flight_packets.size() > 0) {
    //Packet *p = in_flight_packets.front();
    // next_seq_no = p->seq_no;

    // seq_nos_inflight.erase(p->seq_no);
    in_flight_packets.pop_front();
  }
  // if (in_flight_packets.size() != seq_nos_inflight.size()) {
  //   std::cout << "size mismatch (to)!! " << in_flight_packets.size() << " " << seq_nos_inflight.size() << std::endl; fflush(stdout);
  //   assert(false);
  // }
  reset_retx_timeout();

  if (flow_proc_event == NULL) {
    flow_proc_event = new FlowProcessingEvent(get_current_time(), this);
    add_to_event_queue(flow_proc_event);
  }
}

void TurboFlowPerPacketTimeout::reset_retx_timeout() {
  if (retx_event) {
    retx_event->cancelled = true; // Makes sure that the event is not triggered
  }
  // TODO: Be more accurate about the time
  // set_timeout(get_current_time() + retx_timeout);

  if (in_flight_packets.size() > 0) {
    Packet *earliest = in_flight_packets.front();
    double time = earliest->sending_time + retx_timeout;
    //may be neccessary
    // if (time < get_current_time()) {
    //   time = get_current_time() + retx_timeout;
    // }
    set_timeout(time);
  }
}

// uint32_t TurboFlowPerPacketTimeout::get_priority(uint32_t seq) {
//   uint32_t real_prio = TurboFlow::get_priority(seq);
//   // if (priority_backoff > 1e6) {
//   //   return real_prio*1e6; //have a maximum backoff
//   // }
//   // return real_prio*priority_backoff;
//   return real_prio;
// }
