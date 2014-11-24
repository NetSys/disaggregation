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
  Queue(uint32_t id, double rate, uint32_t limit_bytes);
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

  uint32_t b_arrivals, b_departures;
  uint32_t p_arrivals, p_departures;

  double propagation_delay;

};


class PFabricQueue : public Queue {
public:
  PFabricQueue(uint32_t id, double rate, uint32_t limit_bytes);
  void enque(Packet *packet);
  Packet *deque();
};


class ProbDropQueue : public Queue {
  public:
    ProbDropQueue(uint32_t id, double rate, uint32_t limit_bytes,
                  double drop_prob);
    virtual void enque(Packet *packet);

    double drop_prob;
};



#endif
