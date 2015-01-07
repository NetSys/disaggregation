#ifndef QUEUE_H
#define QUEUE_H

#include <deque>
#include <stdint.h>

#define DROPTAIL_QUEUE 1
#define PFABRIC_QUEUE 2

class Node;
class Packet;

class QueueProcessingEvent;
class PacketPropagationEvent;

class Queue {
public:
  Queue(uint32_t id, double rate, uint32_t limit_bytes, int location);
  void set_src_dst(Node *src, Node *dst);
  virtual void enque(Packet *packet);
  virtual Packet *deque();
  virtual void drop(Packet *packet);
  double get_transmission_delay(uint32_t size);

  // Members
  uint32_t id;
  double rate;
  uint32_t limit_bytes;
  std::deque<Packet *> packets;
  uint32_t bytes_in_queue;
  bool busy;
  QueueProcessingEvent *queue_proc_event;


  Node *src;
  Node *dst;

  uint64_t b_arrivals, b_departures;
  uint64_t p_arrivals, p_departures;

  double propagation_delay;
  bool interested;

  uint64_t dropss; uint64_t dropsl; uint64_t dropll;
  uint64_t pkt_drop;
  uint64_t spary_counter;

  int location;
};


class PFabricQueue : public Queue {
public:
  PFabricQueue(uint32_t id, double rate, uint32_t limit_bytes, int location);
  void enque(Packet *packet);
  Packet *deque();
};


class ProbDropQueue : public Queue {
  public:
    ProbDropQueue(uint32_t id, double rate, uint32_t limit_bytes,
                  double drop_prob, int location);
    virtual void enque(Packet *packet);

    double drop_prob;
};



#endif
