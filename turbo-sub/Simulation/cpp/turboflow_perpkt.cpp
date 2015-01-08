#include "turboflow_perpkt.h"
#include "packet.h"
#include "event.h"

extern double get_current_time(); // TODO
extern void add_to_event_queue(Event *);
extern int get_event_queue_size();




/* Per packet timeout implementation Thanks to Kaifei */
/* No Probing or inflation */
TurboFlowPerPacketTimeout::TurboFlowPerPacketTimeout(
  uint32_t id, double start_time, uint32_t size,
  Host *s, Host *d) : TurboFlow(id, start_time, size, s, d) {
  packet_num = 0;
}


uint32_t TurboFlowPerPacketTimeout::select_next_packet() {
  uint32_t seq_to_send = last_unacked_seq;
  while (seq_to_send < size) {
    if (received_ack.count(seq_to_send) != 0) {
      seq_to_send += mss; //packet already received (SACK)
      continue;
    }
    bool done = true;
    for (uint32_t i = head_of_log_idx; i < send_log.size(); i++) {
      if (send_log[i].seq_no == seq_to_send && send_log[i].active) {
        done = false;
        break;
      }
    }
    if (!done) {
      seq_to_send += mss;
      continue;
    }
    return seq_to_send;
  }
  return size; //signal to stop sending
}


void TurboFlowPerPacketTimeout::send_pending_data() {
  if (received_bytes < size) {
    uint32_t seq_to_send = select_next_packet();
    if (seq_to_send >= size)  {// stop sending; Recovery through timeout
      flow_proc_event = NULL;
      return;
    }
    Packet *p = send(seq_to_send);
    SendLogEntry sle;
    sle.seq_no = seq_to_send; sle.timeout = get_current_time() + retx_timeout;
    send_log.push_back(sle);
    packet_num += 1;
    double td = src->queue->get_transmission_delay(p->size);
    flow_proc_event = new FlowProcessingEvent(get_current_time() + td, this);
    add_to_event_queue(flow_proc_event);
    if (retx_event == NULL) {
      reset_retx_timeout();
    }
  }
}

// TODO: To fix
void TurboFlowPerPacketTimeout::handle_timeout() {
  if (!finished) { // Valid timeout condition checking
    // Assert
    assert(retx_event_packet_num == head_of_log_idx);
    if (head_of_log_idx < send_log.size()) {
      assert(send_log[head_of_log_idx].active); // TODO what if assert fails
      send_log[head_of_log_idx].active = false; // TODO what if already false
      head_of_log_idx += 1;
    }
    reset_retx_timeout();
    if (flow_proc_event == NULL) {
      flow_proc_event = new FlowProcessingEvent(get_current_time(), this);
      add_to_event_queue(flow_proc_event);
    }
  }
}


void TurboFlowPerPacketTimeout::reset_retx_timeout() {
  if (retx_event) {
    if(retx_event->unique_id == 5230)
      std::cout << "turboflow_perpkt.cpp:88 canceling 5230\n";
    retx_event->cancelled = true;
    retx_event = NULL;
  }
  if (head_of_log_idx < send_log.size()) {
    SendLogEntry earliest = send_log[head_of_log_idx];
    double retx_time = earliest.timeout;
    retx_event_packet_num = head_of_log_idx;
    assert(retx_time > get_current_time()); // Sanity checks
    set_timeout(retx_time);
  }
  //assert(false); //TODO: if the middle line in handle_timeout stays; this is not true
                    // Think
}

//TODO Add Sack
void TurboFlowPerPacketTimeout::receive_ack(uint32_t ack,
  std::vector<uint32_t> sack_list) {
  this->scoreboard_sack_bytes = sack_list.size() * mss;
  if (ack == size && !finished) {
    finished = true;
    finish_time = get_current_time();
    flow_completion_time = finish_time - start_time;
    FlowFinishedEvent *ev = new FlowFinishedEvent(get_current_time(), this);
    add_to_event_queue(ev);
    cancel_flow_proc_event();
    cancel_retx_event();
    last_unacked_seq = ack;
    send_log.clear();
    return;
  }


  while (last_unacked_seq < ack) {
    received_ack[last_unacked_seq] = true;
    last_unacked_seq += mss;
  }
  for (uint32_t i = 0; i < sack_list.size(); i++) {
    received_ack[sack_list[i]] = true;
  }

  bool is_head_of_log_idx_changed = false;
  while (received_ack.count(send_log[head_of_log_idx].seq_no) > 0) {
    send_log[head_of_log_idx].active = false;
    head_of_log_idx += 1;
    is_head_of_log_idx_changed = true;
  }
  for (uint32_t i = head_of_log_idx; i < send_log.size(); i++) {
    if (received_ack.count(send_log[i].seq_no) > 0) {
      send_log[i].active = false;
    }
  }
  if (is_head_of_log_idx_changed) {
    reset_retx_timeout();
  }
}





/* Proper Timeout */
/*
TurboFlowPerPacketTimeoutWithProbing::TurboFlowPerPacketTimeoutWithProbing(
  uint32_t id, double start_time, uint32_t size,
  Host *s, Host *d) : TurboFlowPerPacketTimeout(id, start_time, size, s, d) {
    this->in_probe_mode = false;
    this->should_send_probe = false;
}

void TurboFlowPerPacketTimeoutWithProbing::send_pending_data() {
  if (received_bytes < size) {
    Packet *p;
    if (should_send_probe) {
      p = send_probe(true); // forward probe
      should_send_probe = false;
    }
    else {
      // uint32_t seq_to_send = next_seq_no;
      // next_seq_no += mss;
      uint32_t seq_to_send = select_next_packet();
      if (seq_to_send >= size)  {//stop sending
        flow_proc_event = NULL;
        return;
      }
      p = send(seq_to_send);
      SendLogEntry sle;
      sle.seq_no = seq_to_send; sle.sending_time = get_current_time();
      in_flight_packets.push_back(sle);
    }
    double td = src->queue->get_transmission_delay(p->size);
    flow_proc_event = new FlowProcessingEvent(get_current_time() + td, this);
    add_to_event_queue(flow_proc_event);
    if (retx_event == NULL) {
      reset_retx_timeout();
    }
  }
}

void TurboFlowPerPacketTimeoutWithProbing::handle_timeout() {
  if (!finished) { // Valid timeout condition checking
    if (in_flight_packets.size() > 0) {
      in_flight_packets.pop_front();
    }
    reset_retx_timeout();
    in_probe_mode = true;
    should_send_probe = true;
    if (flow_proc_event == NULL) {
      flow_proc_event = new FlowProcessingEvent(get_current_time(), this);
      add_to_event_queue(flow_proc_event);
    }
  }
}

void TurboFlowPerPacketTimeoutWithProbing::receive_ack(uint32_t ack) {
  if (ack == size && !finished) {
    finished = true;
    finish_time = get_current_time();
    flow_completion_time = finish_time - start_time;
    FlowFinishedEvent *ev = new FlowFinishedEvent(get_current_time(), this);
    add_to_event_queue(ev);
    cancel_flow_proc_event();
    cancel_retx_event();
    last_unacked_seq = ack;
    in_flight_packets.clear();
    return;
  }
  else if (ack > last_unacked_seq) { // New ack!

    // must remove packets from queue that have been acked since they are no
    // longer inflight
    std::vector<std::list<SendLogEntry>::iterator> to_delete;
    for (std::list<SendLogEntry>::iterator p = in_flight_packets.begin();
      p != in_flight_packets.end(); p++) {
      if (p->seq_no < ack) {
        to_delete.push_back(p);
      }
    }
    for (uint32_t i = 0; i < to_delete.size(); i++) {
      in_flight_packets.erase(to_delete[i]);
    }
    last_unacked_seq = ack;
    reset_retx_timeout();
    this->in_probe_mode = false;
    this->should_send_probe = false; // No need to send a probe now
    if (flow_proc_event == NULL) {
      flow_proc_event = new FlowProcessingEvent(get_current_time(), this);
      add_to_event_queue(flow_proc_event);
    }
  }
}

Packet* TurboFlowPerPacketTimeoutWithProbing::send_probe(bool direction) {
  uint32_t priority;
  Probe *p;
  if (direction) {
    // Probes go at real priority
    priority = get_real_priority(last_unacked_seq);
    p = new Probe(this, priority, 0, direction, hdr_size, src, dst);
    add_to_event_queue(new PacketQueuingEvent(get_current_time(), p, src->queue));
  } else {
    // Probe Ack go at highest priority initialized to 0
    priority = 0;
    p = new Probe(this, priority, 0, direction, hdr_size, dst, src);
    add_to_event_queue(new PacketQueuingEvent(get_current_time(), p, dst->queue));
  }
  // TODO set proper probe id
  return p;
}

void TurboFlowPerPacketTimeoutWithProbing::receive_probe(Probe *p) {
  if (finished) {
    return;
  }
  if (p->direction) { // Have received a probe packet should
    send_probe(false); // Send ack to
  }
  else { // Received reply to a probe
    // TODO: Check if the probe ids match
    in_probe_mode = false;
    should_send_probe = false; // No need to send a probe now
    if (flow_proc_event == NULL) {
      flow_proc_event = new FlowProcessingEvent(get_current_time(), this);
      add_to_event_queue(flow_proc_event);
    }
  }
}

uint32_t TurboFlowPerPacketTimeoutWithProbing::get_priority(uint32_t seq) {
  if (in_probe_mode) { // Real or inflated priority depending on the probe mode
    return INT_MAX;
  } else {
    return get_real_priority(seq);
  }
}

uint32_t TurboFlowPerPacketTimeoutWithProbing::get_real_priority(uint32_t seq) {
  return (size - last_unacked_seq - scoreboard_sack_bytes);
}








TurboFlowPerPacketTimeoutWithRareProbing::TurboFlowPerPacketTimeoutWithRareProbing(
  uint32_t id, double start_time, uint32_t size,
  Host *s, Host *d) : TurboFlowPerPacketTimeoutWithProbing(id, start_time, size, s, d) {
    this->in_probe_mode = false;
    this->should_send_probe = false;
    this->last_probe_sending_time = start_time;
}

void TurboFlowPerPacketTimeoutWithRareProbing::send_pending_data() {
  if (received_bytes < size) {
    Packet *p = NULL;
    if (should_send_probe &&
      get_current_time() >= last_probe_sending_time + retx_timeout) {
        p = send_probe(true); // forward probe
        last_probe_sending_time = get_current_time();
        should_send_probe = false;
    }
    else {
      uint32_t seq_to_send = select_next_packet();
      if (seq_to_send >= size)  {//stop sending
        flow_proc_event = NULL;
        return;
      }
      p = send(seq_to_send);
      SendLogEntry sle;
      sle.seq_no = seq_to_send; sle.sending_time = get_current_time();
      in_flight_packets.push_back(sle);
    }
    double td = src->queue->get_transmission_delay(p->size);
    flow_proc_event = new FlowProcessingEvent(get_current_time() + td, this);
    add_to_event_queue(flow_proc_event);
    if (retx_event == NULL) {
      reset_retx_timeout();
    }
  }
}

*/
