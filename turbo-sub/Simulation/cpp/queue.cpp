#include "queue.h"
#include "packet.h"
#include "event.h"
#include "params.h"
#include <climits>
#include <iostream>
#include <stdlib.h>

extern double get_current_time(); // TODOm
extern void add_to_event_queue(Event *ev);
extern DCExpParams params;

/* Queues */
Queue::Queue(uint32_t id, double rate, uint32_t limit_bytes, int location) {
  this->id = id;
  this->rate = rate; // in bps
  this->limit_bytes = limit_bytes;
  this->bytes_in_queue = 0;
  this->busy = false;
  this->queue_proc_event = NULL;
  //this->packet_propagation_event = NULL;
  this->location = location;

  this->propagation_delay = params.propagation_delay;
  this->p_arrivals = 0; this->p_departures = 0;
  this->b_arrivals = 0; this->b_departures = 0;

  this->dropss = 0; this->dropsl = 0; this->dropll = 0;
  this->pkt_drop = 0;
}

void Queue::set_src_dst(Node *src, Node *dst) {
  this->src = src;
  this->dst = dst;
}

void Queue::enque(Packet *packet) {
  p_arrivals += 1;
  b_arrivals += packet->size;
  if (bytes_in_queue + packet->size <= limit_bytes) {
    packets.push_back(packet);
    bytes_in_queue += packet->size;
  } else {
    pkt_drop++;
    drop(packet);
  }
}

Packet *Queue::deque() {
  if (bytes_in_queue > 0) {
    Packet *p = packets.front();
    packets.pop_front();
    bytes_in_queue -= p->size;
    p_departures += 1;
    b_departures += p->size;
    return p;
  }
  return NULL;
}

void Queue::drop(Packet *packet) {
  delete packet;
}

double Queue::get_transmission_delay(uint32_t size) {
    return size * 8.0 / rate;
}


/* PFabric Queue */
PFabricQueue::PFabricQueue(uint32_t id, double rate, uint32_t limit_bytes, int location)
 : Queue(id, rate, limit_bytes, location) {
}

void PFabricQueue::enque(Packet *packet) {
  p_arrivals += 1;
  b_arrivals += packet->size;
  packets.push_back(packet);
  bytes_in_queue += packet->size;
  if (bytes_in_queue > limit_bytes) {
    uint32_t worst_priority = 0;
    uint32_t worst_index = 0;
    for (uint32_t i = 0; i < packets.size(); i++) {
      if (packets[i]->pf_priority >= worst_priority) {
        worst_priority = packets[i]->pf_priority;
        worst_index = i;
      }
    }
    bytes_in_queue -= packets[worst_index]->size;
    Packet *worst_packet = packets[worst_index];
    bool isLL = false;
    if (worst_packet->size < 5000) { //small flow
      this->dropss += 1;
    }
    else {
      for (uint32_t i = 0; i < packets.size(); i++) {
        if (packets[i]->size > 5000) {
          this->dropll += 1;
          isLL = true;
          break;
        }
      }
      if (!isLL) this->dropsl += 1;
    }
    packets.erase(packets.begin() + worst_index);
    pkt_drop++;
    drop(worst_packet);
  }
}


Packet * PFabricQueue::deque() {
  if (bytes_in_queue > 0) {

    uint32_t best_priority = UINT_MAX;
    //std::cout << "Max:  " << best_priority << std::endl;
    Packet *best_packet = NULL;
    uint32_t best_index = 0;
    for (uint32_t i = 0; i < packets.size(); i++) {
      if (packets[i]->pf_priority <= best_priority) {
        best_priority = packets[i]->pf_priority;
        best_packet = packets[i];
        best_index = i;
      }
    }

    for (uint32_t i = 0; i < packets.size(); i++) {
      if (packets[i]->flow->id == best_packet->flow->id) {
        best_index = i;
        break;
      }
    }
    Packet *p = packets[best_index];
    bytes_in_queue -= p->size;
    packets.erase(packets.begin() + best_index);

    p_departures += 1;
    b_departures += p->size;
    return p;

  } else {
    return NULL;
  }
}


/* Implementation for probabilistically dropping queue */
ProbDropQueue::ProbDropQueue(uint32_t id, double rate, uint32_t limit_bytes,
  double drop_prob, int location)
  : Queue(id, rate, limit_bytes, location) {
  this->drop_prob = drop_prob;
}

void ProbDropQueue::enque(Packet *packet) {
  p_arrivals += 1;
  b_arrivals += packet->size;

  if (bytes_in_queue + packet->size <= limit_bytes) {
    double r = (1.0 * rand()) / (1.0 * RAND_MAX);
    if (r < drop_prob) {
      return;
    }
    packets.push_back(packet);
    bytes_in_queue += packet->size;
    if (!busy) {
      add_to_event_queue(new QueueProcessingEvent(get_current_time(), this));
      busy = true;
    }
  }
}
