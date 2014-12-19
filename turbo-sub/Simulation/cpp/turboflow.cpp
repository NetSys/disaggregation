#include "turboflow.h"
#include "packet.h"
#include "event.h"

extern double get_current_time(); // TODO
extern void add_to_event_queue(Event *);
extern int get_event_queue_size();
extern uint32_t duplicated_packets_received;
/* Implementation for the Turbo flow */

TurboFlow::TurboFlow(uint32_t id, double start_time, uint32_t size,
  Host *s, Host *d) : PFabricFlow(id, start_time, size, s, d) {
  this->in_probe_mode = false;
  this->should_send_probe = false;
}


void TurboFlow::send_pending_data() {
  // Time to send probe
  if (should_send_probe) {
    should_send_probe = false;
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


void TurboFlow::receive_ack(uint32_t ack, std::vector<uint32_t> sack_list) {
  this->scoreboard_sack_bytes = sack_list.size() * mss;

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
    in_probe_mode = false;
    should_send_probe = false; //We need nto send a probe now
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
    in_probe_mode = false;
    should_send_probe = false; // Need not send a probe
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
    Ack *a = (Ack *) p;
    receive_ack(a->seq_no, a->sack_list);
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
  else {
    //recieved duplicated packet
    duplicated_packets_received += 1;
  }

  if (p->seq_no > max_seq_no_recv) {
    max_seq_no_recv = p->seq_no;
  }

  uint32_t s = recv_till;
  bool in_sequence = true;
  std::vector<uint32_t> sack_list;
  while (s <= max_seq_no_recv) {
    if (received.count(s) > 0) {
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
  delete p;
  send_ack(recv_till, sack_list); // Cumulative Ack
}

Packet* TurboFlow::send_probe(bool direction) {
  uint32_t priority = 0;
  Probe *p;
  if (direction) {
    // Probes go at real priority
    priority = Flow::get_priority(last_unacked_seq); //TODO what seq to use??
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

void TurboFlow::handle_timeout()
{
  // TODO don't let inflation rate get too inflated
  in_probe_mode = true;
  should_send_probe = true;
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
  if (in_probe_mode) {
    return (INT_MAX/2) + get_real_priority(seq);;
  } else {
    return get_real_priority(seq);
  }
}

uint32_t TurboFlow::get_real_priority(uint32_t seq) {
  return (size - last_unacked_seq - scoreboard_sack_bytes);
}






/* Implementation for the Turbo Flow that stops on timeout */

TurboFlowStopOnTimeout::TurboFlowStopOnTimeout(
  uint32_t id, double start_time, uint32_t size,
  Host *s, Host *d) : TurboFlow(id, start_time, size, s, d) {
}

void TurboFlowStopOnTimeout::send_pending_data() {
  // Time to send probe
  if (should_send_probe) {
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





/* Per packet timeout implementation Thanks to Kaifei */
/* No Probing or inflation */
// TurboFlowPerPacketTimeout::TurboFlowPerPacketTimeout(
//   uint32_t id, double start_time, uint32_t size,
//   Host *s, Host *d) : TurboFlow(id, start_time, size, s, d) {
// }
//
// uint32_t TurboFlowPerPacketTimeout::select_next_packet() {
//   uint32_t seq_to_send = last_unacked_seq;
//   while (seq_to_send < size) {
//     if (received.count(seq_to_send) != 0) {
//       seq_to_send += mss; //packet already received (SACK)
//       continue;
//     }
//     bool done = true;
//     // This seq_to_send must not be in inflight packets
//     for (std::list<SendLogEntry>::iterator it = in_flight_packets.begin();
//       it != in_flight_packets.end(); it++) {
//       if (it->seq_no == seq_to_send) {
//         done = false;
//         break;
//       }
//     }
//     if (!done) {
//       seq_to_send += mss;
//       continue;
//     }
//     return seq_to_send;
//   }
//   return size; //signal to stop sending
// }
//
// void TurboFlowPerPacketTimeout::send_pending_data() {
//   if (received_bytes < size) {
//     uint32_t seq_to_send = select_next_packet();
//     if (seq_to_send >= size)  {//stop sending
//       flow_proc_event = NULL;
//       return;
//     }
//     Packet *p = send(seq_to_send);
//     SendLogEntry sle;
//     sle.seq_no = seq_to_send; sle.sending_time = get_current_time();
//     in_flight_packets.push_back(sle);
//     double td = src->queue->get_transmission_delay(p->size);
//     flow_proc_event = new FlowProcessingEvent(get_current_time() + td, this);
//     add_to_event_queue(flow_proc_event);
//     if (retx_event == NULL) {
//       reset_retx_timeout();
//     }
//   }
// }
//
// void TurboFlowPerPacketTimeout::handle_timeout() {
//   if (!finished) { // Valid timeout condition checking
//     if (in_flight_packets.size() > 0) {
//       in_flight_packets.pop_front();
//     }
//     reset_retx_timeout();
//     if (flow_proc_event == NULL) {
//       flow_proc_event = new FlowProcessingEvent(get_current_time(), this);
//       add_to_event_queue(flow_proc_event);
//     }
//   }
// }
//
//
// void TurboFlowPerPacketTimeout::reset_retx_timeout() {
//   if (retx_event) {
//     retx_event->cancelled = true;
//     retx_event = NULL;
//   }
//   if (in_flight_packets.size() > 0) {
//     SendLogEntry earliest = in_flight_packets.front();
//     double retx_time = earliest.sending_time + retx_timeout;
//     set_timeout(retx_time);
//   }
// }
//
// void TurboFlowPerPacketTimeout::receive_ack(uint32_t ack) {
//
//   if (ack == size && !finished) {
//     finished = true;
//     finish_time = get_current_time();
//     flow_completion_time = finish_time - start_time;
//     FlowFinishedEvent *ev = new FlowFinishedEvent(get_current_time(), this);
//     add_to_event_queue(ev);
//     cancel_flow_proc_event();
//     cancel_retx_event();
//     last_unacked_seq = ack;
//     in_flight_packets.clear();
//     return;
//   } else if (ack > last_unacked_seq) { // New ack!
//     // must remove packets from queue that have been acked since they are no
//     // longer inflight
//     std::vector<std::list<SendLogEntry>::iterator> to_delete;
//     for (std::list<SendLogEntry>::iterator p = in_flight_packets.begin();
//       p != in_flight_packets.end(); p++) {
//       if (p->seq_no < ack) {
//         to_delete.push_back(p);
//       }
//     }
//     for (uint32_t i = 0; i < to_delete.size(); i++) {
//       in_flight_packets.erase(to_delete[i]);
//     }
//     last_unacked_seq = ack;
//     reset_retx_timeout();
//     if (flow_proc_event == NULL) {
//       flow_proc_event = new FlowProcessingEvent(get_current_time(), this);
//       add_to_event_queue(flow_proc_event);
//     }
//   }
// }










// /* Proper Timeout */
// TurboFlowPerPacketTimeoutWithProbing::TurboFlowPerPacketTimeoutWithProbing(
//   uint32_t id, double start_time, uint32_t size,
//   Host *s, Host *d) : TurboFlowPerPacketTimeout(id, start_time, size, s, d) {
//     this->in_probe_mode = false;
//     this->should_send_probe = false;
// }
//
//
//
//
// void TurboFlowPerPacketTimeoutWithProbing::send_pending_data() {
//   if (received_bytes < size) {
//     Packet *p;
//     if (should_send_probe) {
//       p = send_probe(true); // forward probe
//       should_send_probe = false;
//     }
//     else {
//       // uint32_t seq_to_send = next_seq_no;
//       // next_seq_no += mss;
//       uint32_t seq_to_send = select_next_packet();
//       if (seq_to_send >= size)  {//stop sending
//         flow_proc_event = NULL;
//         return;
//       }
//       p = send(seq_to_send);
//       SendLogEntry sle;
//       sle.seq_no = seq_to_send; sle.sending_time = get_current_time();
//       in_flight_packets.push_back(sle);
//     }
//     double td = src->queue->get_transmission_delay(p->size);
//     flow_proc_event = new FlowProcessingEvent(get_current_time() + td, this);
//     add_to_event_queue(flow_proc_event);
//     if (retx_event == NULL) {
//       reset_retx_timeout();
//     }
//   }
// }
//
// void TurboFlowPerPacketTimeoutWithProbing::handle_timeout() {
//   if (!finished) { // Valid timeout condition checking
//     if (in_flight_packets.size() > 0) {
//       in_flight_packets.pop_front();
//     }
//     reset_retx_timeout();
//     in_probe_mode = true;
//     should_send_probe = true;
//     if (flow_proc_event == NULL) {
//       flow_proc_event = new FlowProcessingEvent(get_current_time(), this);
//       add_to_event_queue(flow_proc_event);
//     }
//   }
// }
//
//
// void TurboFlowPerPacketTimeoutWithProbing::receive(Packet *p) {
//   if (finished) {
//     delete p;
//     return;
//   }
//   // Packet is an ACK
//   if (p->type == ACK_PACKET) {
//     receive_sack(p->seq_no, p->sack_list);
//     this->scoreboard_sack_bytes = ((Ack *) p)->sack_bytes;
//     delete p;
//     return;
//   }
//   // Packet is a probe
//   if (p->type == PROBE_PACKET) {
//     receive_probe((Probe *)p);
//     delete p;
//     return;
//   }
//
//   // Data Packet
//   if (received.count(p->seq_no) == 0) {
//     received[p->seq_no] = true;
//     received_bytes += (p->size - hdr_size);
//   }
//   else {
//     //recieved duplicated packet
//     duplicated_packets_received += 1;
//   }
//
//   if (p->seq_no > max_seq_no_recv) {
//     max_seq_no_recv = p->seq_no;
//   }
//   //if (id == 1) {
//   //  std::cout << 1000000.0 * get_current_time() << " Received " << p->seq_no <<
//   //    " from " << id << std::endl;
//   //}
//
//   // Determing which ack to send
//   uint32_t s = recv_till;
//   bool in_sequence = true;
//   uint32_t sack_bytes = 0;
//   while (s <= max_seq_no_recv) {
//     if (received.count(s) > 0) {
//       //printf("s %d: count:%d\n", s, received.count(s));
//       if (in_sequence) {
//         recv_till += mss;
//       } else {
//         sack_bytes += mss;
//       }
//     } else {
//       in_sequence = false;
//     }
//     s += mss;
//   }
//   delete p;
//   send_ack(recv_till, sack_bytes); // Cumulative Ack
// }
//
//
// void TurboFlowPerPacketTimeoutWithProbing::receive_sack(
//   uint32_t ack, std::vector<uint32_t> sack_list) {
//   if (ack == size && !finished) {
//     finished = true;
//     finish_time = get_current_time();
//     flow_completion_time = finish_time - start_time;
//     FlowFinishedEvent *ev = new FlowFinishedEvent(get_current_time(), this);
//     add_to_event_queue(ev);
//     cancel_flow_proc_event();
//     cancel_retx_event();
//     last_unacked_seq = ack;
//     in_flight_packets.clear();
//     return;
//   }
//
//
//
//   else { // Flow hasn't finished; process ack
//     if (ack > last_unacked_seq) { // New ack!
//       // must remove packets from queue that have been acked since they are no longer inflight
//       std::vector<std::list<SendLogEntry>::iterator> to_delete;
//       for (std::list<SendLogEntry>::iterator p = in_flight_packets.begin();
//         p != in_flight_packets.end(); p++) {
//         if (p->seq_no < ack) {
//           to_delete.push_back(p);
//         }
//       }
//       for (uint32_t i = 0; i < to_delete.size(); i++) {
//         in_flight_packets.erase(to_delete[i]);
//       }
//       last_unacked_seq = ack;
//       reset_retx_timeout();
//       this->in_probe_mode = false;
//       this->should_send_probe = false; // No need to send a probe now
//     }
//     if (sack_list.size() > 0) {
//       std::vector<std::list<SendLogEntry>::iterator> to_delete;
//       for each seq in sack_list:
//         for (std::list<SendLogEntry>::iterator p = in_flight_packets.begin();
//           p != in_flight_packets.end(); p++) {
//           if (p->seq_no == seq) {
//             to_delete.push_back(p);
//           }
//         }
//       }
//       for (uint32_t i = 0; i < to_delete.size(); i++) {
//         in_flight_packets.erase(to_delete[i]);
//       }
//     }
//   }
// }
//
// Packet* TurboFlowPerPacketTimeoutWithProbing::send_probe(bool direction) {
//   uint32_t priority;
//   Probe *p;
//   if (direction) {
//     // Probes go at real priority
//     priority = get_real_priority(last_unacked_seq);
//     p = new Probe(this, priority, 0, direction, hdr_size, src, dst);
//     add_to_event_queue(new PacketQueuingEvent(get_current_time(), p, src->queue));
//   } else {
//     // Probe Ack go at highest priority initialized to 0
//     priority = 0;
//     p = new Probe(this, priority, 0, direction, hdr_size, dst, src);
//     add_to_event_queue(new PacketQueuingEvent(get_current_time(), p, dst->queue));
//   }
//   // TODO set proper probe id
//   return p;
// }
//
//
// void TurboFlowPerPacketTimeoutWithProbing::receive_probe(Probe *p) {
//   if (finished) {
//     return;
//   }
//   if (p->direction) { // Have received a probe packet should
//     send_probe(false); // Send ack to
//   }
//   else { // Received reply to a probe
//     // TODO: Check if the probe ids match
//     in_probe_mode = false;
//     should_send_probe = false; // No need to send a probe now
//     if (flow_proc_event == NULL) {
//       flow_proc_event = new FlowProcessingEvent(get_current_time(), this);
//       add_to_event_queue(flow_proc_event);
//     }
//   }
// }
//
//
// uint32_t TurboFlowPerPacketTimeoutWithProbing::get_priority(uint32_t seq) {
//   if (in_probe_mode) { // Real or inflated priority depending on the probe mode
//     return INT_MAX;
//   } else {
//     return get_real_priority(seq);
//   }
// }
//
//
// uint32_t TurboFlowPerPacketTimeoutWithProbing::get_real_priority(uint32_t seq) {
//   return (size - last_unacked_seq - scoreboard_sack_bytes);
// }







//
// TurboFlowPerPacketTimeoutWithRareProbing::TurboFlowPerPacketTimeoutWithRareProbing(
//   uint32_t id, double start_time, uint32_t size,
//   Host *s, Host *d) : TurboFlowPerPacketTimeoutWithProbing(id, start_time, size, s, d) {
//     this->in_probe_mode = false;
//     this->should_send_probe = false;
//     this->last_probe_sending_time = start_time;
// }
//
// void TurboFlowPerPacketTimeoutWithRareProbing::send_pending_data() {
//   if (received_bytes < size) {
//     Packet *p = NULL;
//     if (should_send_probe &&
//       get_current_time() >= last_probe_sending_time + retx_timeout) {
//         p = send_probe(true); // forward probe
//         last_probe_sending_time = get_current_time();
//         should_send_probe = false;
//     }
//     else {
//       uint32_t seq_to_send = select_next_packet();
//       if (seq_to_send >= size)  {//stop sending
//         flow_proc_event = NULL;
//         return;
//       }
//       p = send(seq_to_send);
//       SendLogEntry sle;
//       sle.seq_no = seq_to_send; sle.sending_time = get_current_time();
//       in_flight_packets.push_back(sle);
//     }
//     double td = src->queue->get_transmission_delay(p->size);
//     flow_proc_event = new FlowProcessingEvent(get_current_time() + td, this);
//     add_to_event_queue(flow_proc_event);
//     if (retx_event == NULL) {
//       reset_retx_timeout();
//     }
//   }
// }


TurboFlowLongFlowsGetLowPriority::TurboFlowLongFlowsGetLowPriority(
  uint32_t id, double start_time, uint32_t size,
  Host *s, Host *d) : TurboFlow(id, start_time, size, s, d) {
}

uint32_t
TurboFlowLongFlowsGetLowPriority::get_priority(uint32_t seq) {
  double long_flow_cutoff = 1000000;
  if (this->size >= long_flow_cutoff) {
    return (INT_MAX/2) + get_real_priority(seq);
  }
  else {
    return TurboFlow::get_priority(seq);
  }
}
