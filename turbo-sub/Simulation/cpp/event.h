//
//  event.h
//  TurboCpp
//
//  Created by Gautam Kumar on 3/9/14.
//
//

#ifndef EVENT_H
#define EVENT_H

#include <iostream>
#include <math.h>
#include "node.h"
#include "queue.h"
#include "flow.h"
#include <queue>
#include "random_variable.h"
//TODO import globals

#define FLOW_ARRIVAL 0
#define PACKET_QUEUING 1
#define PACKET_ARRIVAL 2
#define QUEUE_PROCESSING 3
#define RETX_TIMEOUT 5
#define FLOW_FINISHED 6
#define FLOW_PROCESSING 7

#define FLOW_CREATION_EVENT 8

#define LOGGING 9




class Event {
public:
  Event(uint32_t type, double time);
  virtual ~Event();
  bool operator == (const Event& e) const {
    return (time == e.time && type == e.type);
  }
  bool operator < (const Event& e) const {
    if (time < e.time) return true;
    else if (time == e.time && type < e.type) return true;
    else return false;
  }
  bool operator > (const Event& e) const {
    if (time > e.time) return true;
    else if (time == e.time && type > e.type) return true;
    else return false;
  }

  virtual void process_event() = 0;

  uint32_t unique_id;
  static uint32_t instance_count;

  uint32_t type;
  double time;
  bool cancelled;
};

struct EventComparator
{
    bool operator() (Event *a, Event *b) {
      if (fabs(a->time - b->time) < 1e-12) {
        return a->type > b->type;
      } else {
        return a->time > b->time;
      }
    }
};



//A flow arrival event
class FlowArrivalEvent : public Event {
public:
  FlowArrivalEvent(double time, Flow *flow);
  ~FlowArrivalEvent();
  void process_event();
  Flow *flow;
};

//A flow arrival event
class FlowProcessingEvent : public Event {
public:
  FlowProcessingEvent(double time, Flow *flow);
  ~FlowProcessingEvent();

  void process_event();
  Flow *flow;
};

//A flow finished event
class FlowFinishedEvent : public Event {
public:
  FlowFinishedEvent(double time, Flow *flow);
  ~FlowFinishedEvent();
  void process_event();
  Flow *flow;
};


//A flow finished event
class DDCTestFlowFinishedEvent : public FlowFinishedEvent {
public:
  DDCTestFlowFinishedEvent(double time, Flow *flow);
  ~DDCTestFlowFinishedEvent();
  void process_event();
};



// packet gets queued
class PacketQueuingEvent : public Event {
public:
  PacketQueuingEvent(double time, Packet *packet, Queue *queue);
  ~PacketQueuingEvent();
  void process_event();
  Packet *packet;
  Queue *queue;
};

// packet arrival
class PacketArrivalEvent : public Event {
public:
  PacketArrivalEvent(double time, Packet *packet);
  ~PacketArrivalEvent();
  void process_event();
  Packet *packet;
};

class QueueProcessingEvent : public Event {
public:
  QueueProcessingEvent(double time, Queue *queue);
  ~QueueProcessingEvent();
  void process_event();
  Queue *queue;
};

class RetxTimeoutEvent : public Event {
public:
  RetxTimeoutEvent(double time, Flow *flow);
  ~RetxTimeoutEvent();
  void process_event();
  Flow *flow;
};


//A flow arrival event Only used for FlowCreation
class FlowCreationForInitializationEvent : public Event {
public:
  FlowCreationForInitializationEvent(double time, Host *src, Host *dst,
                                     EmpiricalRandomVariable *nv_bytes,
                                     ExponentialRandomVariable *nv_intarr);
  ~FlowCreationForInitializationEvent();
  void process_event();
  Host *src;
  Host *dst;
  EmpiricalRandomVariable *nv_bytes;
  ExponentialRandomVariable *nv_intarr;
};

class FlowCreationForInitializationEventWithTimeLimit : public FlowCreationForInitializationEvent {
public:
  double time_limit;
  FlowCreationForInitializationEventWithTimeLimit(
    double time_limit, double time, Host *src, Host *dst,
    EmpiricalRandomVariable *nv_bytes, ExponentialRandomVariable *nv_intarr
  );
  void process_event();
};

class LoggingEvent : public Event {
public:
  LoggingEvent(double time);
  ~LoggingEvent();
  void process_event();
};


// packet gets queued
class DDCHostPacketQueuingEvent : public PacketQueuingEvent {
public:
  DDCHostPacketQueuingEvent(double time, Packet *packet, Queue *queue);
  ~DDCHostPacketQueuingEvent();
  void process_event();
};

class DDCHostQueueProcessingEvent : public QueueProcessingEvent {
public:
  DDCHostQueueProcessingEvent(double time, Queue *queue);
  ~DDCHostQueueProcessingEvent();
  void process_event();
};

#endif /* defined(EVENT_H) */
