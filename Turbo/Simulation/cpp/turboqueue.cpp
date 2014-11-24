#include "turboqueue.h"
#include "packet.h"
#include "event.h"
#include "params.h"
#include <climits>
#include <iostream>
#include <stdlib.h>

extern double get_current_time(); // TODOm
extern void add_to_event_queue(Event *ev);
extern DCExpParams params;

/* Turbo Queue */
TurboQueue::TurboQueue(uint32_t id, double rate, uint32_t limit_bytes)
 : Queue(id, rate, limit_bytes) {
   interested = false;
}
void TurboQueue::enque(Packet *packet) {
  if (interested) std::cout << 1000000.0 * get_current_time() << " " << id << " Enqueing " << packet->flow->id << " " << packet->seq_no << "\n";

  // if (interested && packet->flow->id == 0) {
  //   std::cout << "enq 0: ";
  //   for (uint32_t i = 0; i < packets.size(); i++) {
  //     std::cout << packets[i]->flow->id << " ";
  //   }
  //   std::cout << "; " << busy << "\n";
  // }

  p_arrivals += 1;
  b_arrivals += packet->size;
  packets.push_back(packet);
  bytes_in_queue += packet->size;
  if (bytes_in_queue > limit_bytes) {
    uint32_t worst_priority = 0;
    Packet *worst_packet = NULL;
    uint32_t worst_index = 0;
    for (uint32_t i = 0; i < packets.size(); i++) {
      if (packets[i]->pf_priority >= worst_priority) {
        worst_priority = packets[i]->pf_priority;
        worst_packet = packets[i];
        worst_index = i;
      }
    }
    for (uint32_t i = 0; i < packets.size(); i++) {
      if (packets[i]->flow->id == worst_packet->flow->id) {// Match flow
        if (packets[i]->seq_no >= worst_packet->seq_no) {
          // Last packet
          worst_packet = packets[i];
          worst_index = i;
        }
      }
    }
    bytes_in_queue -= packets[worst_index]->size;
    packets.erase(packets.begin() + worst_index);

    // if (interested) std::cout << 1e6*get_current_time() << " Drop Happened " << worst_packet->flow->id << " " << worst_packet->seq_no << "\n";

    drop(worst_packet);

  }

}

Packet * TurboQueue::deque() {
  // for (uint32_t )

  if (bytes_in_queue > 0) {
    uint32_t best_priority = UINT_MAX;
    Packet *best_packet = NULL;
    uint32_t best_index = 0;

    // Find the least priority amongst all packets
    for (uint32_t i = 0; i < packets.size(); i++) {
      if (packets[i]->pf_priority <= best_priority) {
        best_priority = packets[i]->pf_priority;
        best_packet = packets[i];
        best_index = i;
      }
    }
    // Find the least seq no in the above flow
    for (uint32_t i = 0; i < packets.size(); i++) {
      if (packets[i]->flow->id == best_packet->flow->id) {
        if (packets[i]->seq_no <= best_packet->seq_no) {
          best_packet = packets[i];
          best_index = i;
        }
      }
    }

    Packet *p = best_packet;
    bytes_in_queue -= p->size;
    packets.erase(packets.begin() + best_index);

    p_departures += 1;
    b_departures += p->size;

    if (interested) {
      std::cout << 1e6 * get_current_time() << " " << id << " Dequeing " << p->seq_no << " " << p->flow->id << "\n";

    }
    return p;
  }
  else {
    return NULL;
  }
}
