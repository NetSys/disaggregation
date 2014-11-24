#ifndef TURBO_QUEUE_H
#define TURBO_QUEUE_H

#include "queue.h"
#include <deque>
#include <stdint.h>


class TurboQueue: public Queue {
public:
  TurboQueue(uint32_t id, double rate, uint32_t limit_bytes);
  virtual void enque(Packet *packet);
  Packet *deque();
};

#endif
