#include "pacedflow.h"
#include "event.h"
#include "packet.h"

extern double get_current_time(); // TODOm
extern void add_to_event_queue(Event *);
extern int get_event_queue_size();


/* Implementation for a full blast flow that paces */
PacedFlow::PacedFlow(
  uint32_t id, double start_time,
  uint32_t size,
  Host *s, Host *d, double rate) : Flow(id, start_time, size, s, d) {
  this->rate = rate;
  assert(rate <= 1.0);
}

void PacedFlow::send_pending_data() {
  if (received_bytes < size) {
    //std::cout << "Sending Pending Data" << std::endl;
    if (next_seq_no + mss > size) {
      next_seq_no = last_unacked_seq;
    }
    uint32_t seqn = next_seq_no;
    if (seqn + mss > size) {
      return;
    }
    next_seq_no = seqn + mss;
    if (received.count(seqn) == 0) {
      //std::cout << get_current_time() << " Enqueing " << seqn << "\n";
      uint32_t priority = get_priority(seqn);
      Packet *p = new Packet(get_current_time(), this, seqn, \
                     priority, mss + hdr_size, \
                     src, dst);

      double td = src->queue->get_transmission_delay(p->size);
      double wait = td / rate;
      add_to_event_queue(new PacketQueuingEvent(get_current_time(),
        p, src->queue));
      add_to_event_queue(new FlowProcessingEvent(get_current_time() + wait,
        this));
    } else {
      send_pending_data();
    }
  }
}


void PacedFlow::receive_ack(uint32_t ack, std::vector<uint32_t> sack_list) {
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
  }

  if (ack == size && !finished) {
    finished = true;
    finish_time = get_current_time();
    flow_completion_time = finish_time - start_time;
    FlowFinishedEvent *ev = new FlowFinishedEvent(get_current_time(), this);
    add_to_event_queue(ev);
  }
}


void PacedFlow::handle_timeout() {
  // Has no timeouts
  return;
}


FullBlastPacedFlow::FullBlastPacedFlow(uint32_t id, double start_time,
  uint32_t size,
  Host *s, Host *d) : PacedFlow(id, start_time, size, s, d, 1.0) {
}



JitteredPacedFlow::JitteredPacedFlow(
  uint32_t id, double start_time,uint32_t size,
  Host *s, Host *d, double rate) : PacedFlow(id, start_time, size, s, d, rate) {
}

void JitteredPacedFlow::send_pending_data() {
  if (received_bytes < size) {
    //std::cout << "Sending Pending Data" << std::endl;
    if (next_seq_no + mss > size) {
      next_seq_no = last_unacked_seq;
    }
    uint32_t seqn = next_seq_no;
    if (seqn + mss > size) {
      return;
    }
    next_seq_no = seqn + mss;
    if (received.count(seqn) == 0) {
      //std::cout << get_current_time() << " Enqueing " << seqn << "\n";
      uint32_t priority = get_priority(seqn);
      Packet *p = new Packet(get_current_time(), this, seqn, \
                     priority, mss + hdr_size, \
                     src, dst);

      double td = src->queue->get_transmission_delay(p->size);
      double wait = td / rate;
      double jitter = (wait - td) * rand() / RAND_MAX;
      add_to_event_queue(new PacketQueuingEvent(get_current_time() + jitter,
        p, src->queue));
      add_to_event_queue(new FlowProcessingEvent(get_current_time() + wait,
        this));
    } else {
      send_pending_data();
    }
  }
}
