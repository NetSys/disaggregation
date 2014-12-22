//
//  event.cpp
//  TurboCpp
//
//  Created by Gautam Kumar on 3/9/14.
//
//

#include "event.h"
#include "packet.h"
#include "topology.h"
#include "params.h"
#include "factory.h"


extern Topology *topology;
extern std::priority_queue<Event *, std::vector<Event *>,
                           EventComparator> event_queue;
extern double current_time;
extern DCExpParams params;
extern std::deque<Event *> flow_arrivals;
extern std::deque<Flow *> flows_to_schedule;

extern uint32_t num_outstanding_packets;
extern uint32_t max_outstanding_packets;


void add_to_event_queue(Event *ev) {
  event_queue.push(ev);
}

int get_event_queue_size() {
  return event_queue.size();
}

double get_current_time() {
  return current_time; // in us
}



Event::Event(uint32_t type, double time) {
  this->type = type;
  this->time = time;
  this->cancelled = false;
}

Event::~Event() {
}


/* Flow Arrival */
FlowArrivalEvent::FlowArrivalEvent(double time, Flow *flow)
  : Event(FLOW_ARRIVAL, time) {
  this->flow = flow;
}
FlowArrivalEvent::~FlowArrivalEvent() {
}
void FlowArrivalEvent::process_event() {
  //Flows start at line rate; so schedule a packet to be transmitted
  //First packet scheduled to be queued

  num_outstanding_packets += (this->flow->size / this->flow->mss);
  if (num_outstanding_packets > max_outstanding_packets) {
    max_outstanding_packets = num_outstanding_packets;
  }
  this->flow->start_flow();
  if (flow_arrivals.size() > 0) {
    add_to_event_queue(flow_arrivals.front());
    flow_arrivals.pop_front();
  }
}



/* Flow Processing */
FlowProcessingEvent::FlowProcessingEvent(double time, Flow *flow)
  : Event(FLOW_PROCESSING, time) {
  this->flow = flow;
}
FlowProcessingEvent::~FlowProcessingEvent() {
  if (flow->flow_proc_event == this) {
    flow->flow_proc_event = NULL;
  }
}
void FlowProcessingEvent::process_event() {
  this->flow->send_pending_data();
}



/* Flow Finished */
FlowFinishedEvent::FlowFinishedEvent(double time, Flow *flow)
 : Event(FLOW_FINISHED, time) {
  this->flow = flow;
}
FlowFinishedEvent::~FlowFinishedEvent() {
}
void FlowFinishedEvent::process_event() {
//  std::cout
//    << "event.cpp::FlowFinishedEvent(): "
//    << "id:" << flow->id << " "
//    << "sz:" << flow->size << " "
//    << "src:" << flow->src->id << " "
//    << "dst:" << flow->dst->id << " "
//    << "strt:" << 1000000 * flow->start_time << " "
//    << "end:" << 1000000 * flow->finish_time << " "
//    << "fct:" << 1000000.0 * flow->flow_completion_time << " "
//    << "orcl:" << topology->get_oracle_fct(flow) << " "
//    << "rate:" << 1000000 * flow->flow_completion_time / topology->get_oracle_fct(flow)
//    << std::endl;
}


/* Packet Queuing */
PacketQueuingEvent::PacketQueuingEvent(double time, Packet *packet,
  Queue *queue) : Event(PACKET_QUEUING, time) {
  this->packet = packet;
  this->queue = queue;
}
PacketQueuingEvent::~PacketQueuingEvent() {
}
void PacketQueuingEvent::process_event() {
  if (!queue->busy) {
    queue->queue_proc_event = new QueueProcessingEvent(get_current_time(), queue);
    add_to_event_queue(queue->queue_proc_event);
    queue->busy = true;
  }
  queue->enque(packet);
}



/* Packet Arrival */
PacketArrivalEvent::PacketArrivalEvent(double time, Packet *packet)
  : Event(PACKET_ARRIVAL, time) {
  this->packet = packet;
}
PacketArrivalEvent::~PacketArrivalEvent() {
}
void PacketArrivalEvent::process_event() {
  packet->flow->receive(packet);
}



/* Queue Processing */
QueueProcessingEvent::QueueProcessingEvent(double time, Queue *queue)
  : Event(QUEUE_PROCESSING, time) {
  this->queue = queue;
}
QueueProcessingEvent::~QueueProcessingEvent() {
  if (queue->queue_proc_event == this) {
    queue->queue_proc_event = NULL;
  }
}
void QueueProcessingEvent::process_event() {
  Packet *packet = queue->deque();
  if (packet) {
    queue->busy = true;
    Queue *next_hop = topology->get_next_hop(packet, queue);
    double td = queue->get_transmission_delay(packet->size);
    double pd = queue->propagation_delay;
    //double additional_delay = 1e-10;
    queue->queue_proc_event = new QueueProcessingEvent(time + td, queue);
    add_to_event_queue(queue->queue_proc_event);
    if (next_hop == NULL) {
      add_to_event_queue(new PacketArrivalEvent(time + td + pd, packet));
    } else {
      if (params.cut_through == 1) {
        double cut_through_delay =
          queue->get_transmission_delay(packet->flow->hdr_size);
        add_to_event_queue(new PacketQueuingEvent(time + cut_through_delay + pd,
                                                  packet, next_hop));
      } else {
        add_to_event_queue(new PacketQueuingEvent(time + td + pd,
                                                  packet, next_hop));
      }
    }
  } else {
    queue->busy = false;
    queue->queue_proc_event = NULL;
  }
}



/* Retx Timeout */
RetxTimeoutEvent::RetxTimeoutEvent(double time, Flow *flow)
  : Event(RETX_TIMEOUT, time) {
  this->flow = flow;
}
RetxTimeoutEvent::~RetxTimeoutEvent() {
  if (flow->retx_event == this) {
    flow->retx_event = NULL;
  }
}
void RetxTimeoutEvent::process_event() {
  flow->handle_timeout();
}


/* Flow Arrival */
FlowCreationForInitializationEvent::FlowCreationForInitializationEvent(
  double time, Host *src, Host *dst,
  EmpiricalRandomVariable *nv_bytes, ExponentialRandomVariable *nv_intarr)
  : Event(FLOW_CREATION_EVENT, time) {
  this->src = src;
  this->dst = dst;
  this->nv_bytes = nv_bytes;
  this->nv_intarr = nv_intarr;
}

FlowCreationForInitializationEvent::~FlowCreationForInitializationEvent() {
}
void FlowCreationForInitializationEvent::process_event() {
  uint32_t id = flows_to_schedule.size();
  uint32_t size = nv_bytes->value() * 1460;
  flows_to_schedule.push_back(Factory::get_flow(id, time, size,
                                                src, dst, params.flow_type));
  //std::cout << "event.cpp::FlowCreation:" << 1000000.0 * time << " Generating new flow " << id << " of size "
  // << size << " between " << src->id << " " << dst->id << "\n";

  double tnext = time + nv_intarr->value();
  add_to_event_queue(new FlowCreationForInitializationEvent(tnext,
                                         src, dst,
                                         nv_bytes, nv_intarr));
}


FlowCreationForInitializationEventWithTimeLimit::FlowCreationForInitializationEventWithTimeLimit(
  double time_limit, double time, Host *src, Host *dst,
  EmpiricalRandomVariable *nv_bytes, ExponentialRandomVariable *nv_intarr
)
  : FlowCreationForInitializationEvent(time, src, dst, nv_bytes, nv_intarr) {
    this->time_limit = time_limit;
}

void FlowCreationForInitializationEventWithTimeLimit::process_event() {
  uint32_t id = flows_to_schedule.size();
  uint32_t size = nv_bytes->value() * 1460;

  flows_to_schedule.push_back(
    Factory::get_flow(id, time, size, src, dst, params.flow_type)
  );

  std::cout << 1000000.0 * time << " Generating new flow " << id << " of size "
   << size << " between " << src->id << " " << dst->id << "\n";

  double tnext = time + nv_intarr->value();
  if (tnext < time_limit)
    add_to_event_queue(
      new FlowCreationForInitializationEventWithTimeLimit(
        time_limit, tnext, src, dst, nv_bytes, nv_intarr
      )
    );
}


LoggingEvent::LoggingEvent(double time) : Event(LOGGING, time){
}

LoggingEvent::~LoggingEvent() {
}

void LoggingEvent::process_event() {
  double current_time = get_current_time();
  bool finished_simulation = true;
  uint32_t second_num_outstanding = 0;
  uint32_t num_unfinished_flows = 0;
  uint32_t started_flows = 0;
  for (uint32_t i = 0; i < flows_to_schedule.size(); i++) {
    Flow *f = flows_to_schedule[i];
    if (finished_simulation && !f->finished) {
      finished_simulation = false;
    }
    if (f->start_time < current_time) {
      second_num_outstanding += (f->size - f->received_bytes);
      started_flows ++;
      if (!f->finished) {
        num_unfinished_flows ++;
      }
    }
  }
  std::cout << current_time*1000000.0
    << " MaxPacketOutstanding " << max_outstanding_packets
    << " NumPacketOutstanding " << num_outstanding_packets
    << " NumUnfinishedFlows " << num_unfinished_flows
    << " StartedFlows " << started_flows << "\n";

  if (!finished_simulation) {
    add_to_event_queue(new LoggingEvent(current_time + 0.01));
  }
}
