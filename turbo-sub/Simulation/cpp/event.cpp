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
#include <iomanip>


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

uint32_t Event::instance_count = 0;

Event::Event(uint32_t type, double time) {
  this->type = type;
  this->time = time;
  this->cancelled = false;
  this->unique_id = Event::instance_count++;
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
//    << "rate:" << 1000000 * flow->flow_completion_time / topology->get_oracle_fct(flow) << " "
//    << "infl:" << flow->total_pkt_sent << "/" << (flow->size/flow->mss)
//    << std::endl;
}



/* Flow Finished */
DDCTestFlowFinishedEvent::DDCTestFlowFinishedEvent(double time, Flow *flow)
 : FlowFinishedEvent(time, flow) {
}

DDCTestFlowFinishedEvent::~DDCTestFlowFinishedEvent() {
}
void DDCTestFlowFinishedEvent::process_event() {
//    std::cout
//      << "event.cpp::FlowFinishedEvent(): "
//      << "id:" << flow->id << " "
//      << "sz:" << flow->size << " "
//      << "src:" << flow->src->id << " "
//      << "dst:" << flow->dst->id << " "
//      << "strt:" << (int)(1000000 * flow->start_time) << " "
//      << "end:" << (int)(1000000 * flow->finish_time) << " "
//      << "fct:" << std::setprecision(2) << 1000000.0 * flow->flow_completion_time << " "
//      << "orcl:" << topology->get_oracle_fct(flow) << " "
//      << "rate:" << std::setprecision(2) << 1000000 * flow->flow_completion_time / topology->get_oracle_fct(flow) << " "
//      << "infl:" << flow->total_pkt_sent << "/" << (flow->size/flow->mss) << " "
//      << "drp:" << flow->data_pkt_drop << "/" << flow->pkt_drop
//      << std::endl;
  if(Factory::flow_counter < params.num_flows_to_run){
    Flow* flow = Factory::get_flow(get_current_time(), this->flow->size, this->flow->src, this->flow->dst, params.flow_type);
    flow->useDDCTestFlowFinishedEvent = true;
    flows_to_schedule.push_back(flow);
    Event * event = new FlowArrivalEvent(flow->start_time, flow);
    add_to_event_queue(event);
  }
}



/* Packet Queuing */
PacketQueuingEvent::PacketQueuingEvent(double time, Packet *packet,
  Queue *queue) : Event(PACKET_QUEUING, time) {
  //if(packet->flow->id == 61 || packet->flow->id == 70)
  //  std::cout << "PacketQueuingEvent::PacketQueuingEvent() fid:" << packet->flow->id << " seq:" << packet->seq_no << " ptr:" << packet << "\n";
  this->packet = packet;
  this->queue = queue;
  if(this->queue->unique_id == 0 && this->unique_id == 8276){
    std::cout << get_current_time() << " event.cpp:160 pktqevt,cons @q " << queue->unique_id << " ptr:" << queue << " evt eid:" << this->unique_id << " ptr:" << this << "\n";
    assert(false);
  }
}

PacketQueuingEvent::~PacketQueuingEvent() {
}

void PacketQueuingEvent::process_event() {
//  if(this->packet->unique_id == 761){
//    std::cout << get_current_time() << " event.cpp:173 packet queuing pkt:" << packet << " pid:" << packet->unique_id << " to q:" << queue << " qid:" << queue->unique_id <<
//    "event ptr:" << this << " eid:" << this->unique_id << " q->busy:" << queue->busy;
//    if (queue->busy){
//      std::cout << " preempt?" << (this->packet->pf_priority < queue->packet_transmitting->pf_priority);
//    }
//    std::cout << "\n";
//  }

  if (!queue->busy || ( params.preemptive_queue && this->packet->pf_priority < queue->packet_transmitting->pf_priority) ) {
    if(queue->busy && queue->queue_proc_event->unique_id == 7394)
      std::cout << get_current_time() << " event.cpp:176" << " this:" << this << " eid:" << this->unique_id << " preempting evt:" << queue->queue_proc_event->unique_id << " ptr:" << queue->queue_proc_event << "\n";
    queue->preempt_current_transmission();
    queue->queue_proc_event = new QueueProcessingEvent(get_current_time(), queue);
    add_to_event_queue(queue->queue_proc_event);
    queue->busy = true;
    queue->packet_transmitting = packet;
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
//  if (this->unique_id == 5230)
//    std::cout << "~~~~~~~~~~~~~~~QueueProcessingEvent()\n";
  if (queue->queue_proc_event == this) {
//    if (this->unique_id == 5230)
//      std::cout << "setting NULL\n";
    queue->queue_proc_event = NULL;
  }
}
void QueueProcessingEvent::process_event() {

  Packet *packet = queue->deque();
  if (packet) {
    queue->busy = true;
    queue->busy_events.clear();
    queue->packet_transmitting = packet;
    Queue *next_hop = topology->get_next_hop(packet, queue);
    double td = queue->get_transmission_delay(packet->size);
    double pd = queue->propagation_delay;
    //double additional_delay = 1e-10;
    queue->queue_proc_event = new QueueProcessingEvent(time + td, queue);
//    if(queue->unique_id == 329)
//      std::cout << get_current_time() << " event.cpp:222 this:" << this << " id:" << this->unique_id << " q:" << queue->unique_id << " qptr:" << queue <<  " add QueueProcessingEvent("<<(time + td)<<") evt ptr:"
//      << queue->queue_proc_event << " id:" << queue->queue_proc_event->unique_id << " pkt ptr:" << packet << " transmitting:" << queue->packet_transmitting << "\n";
    add_to_event_queue(queue->queue_proc_event);
    queue->busy_events.push_back(queue->queue_proc_event);
    if (next_hop == NULL) {
      Event* arrival_evt = new PacketArrivalEvent(time + td + pd, packet);
      add_to_event_queue(arrival_evt);
      queue->busy_events.push_back(arrival_evt);
    } else {
      Event* queuing_evt = NULL;
      if (params.cut_through == 1) {
        double cut_through_delay =
          queue->get_transmission_delay(packet->flow->hdr_size);
        queuing_evt = new PacketQueuingEvent(time + cut_through_delay + pd, packet, next_hop);
      } else {
        queuing_evt = new PacketQueuingEvent(time + td + pd, packet, next_hop);
      }
//      if(packet->unique_id == 761)
//        std::cout << get_current_time() << " event.cpp:238 this:" << this << " id:" << this->unique_id << " q:" << queue->unique_id << " qptr:" << queue <<  " add PacketQueuingEvent("<< queuing_evt->time
//        <<") evt ptr:" << queuing_evt << " pkt ptr:" << packet << " pid:" << packet->unique_id << " next hop:" << next_hop << " qid:" << next_hop->unique_id << "\n";

      add_to_event_queue(queuing_evt);
      queue->busy_events.push_back(queuing_evt);
    }
  } else {
//    if(queue->unique_id == 171)
//      std::cout << get_current_time() << " event.cpp:213 this:" << this << " q:" << queue->unique_id << " qptr:" << queue <<  "\n";
    queue->busy = false;
    queue->busy_events.clear();
    queue->packet_transmitting = NULL;
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
  this->ttl = 1e10;
}

LoggingEvent::LoggingEvent(double time, double ttl) : Event(LOGGING, time){
  this->ttl = ttl;
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
  std::cout << current_time
    << " MaxPacketOutstanding " << max_outstanding_packets
    << " NumPacketOutstanding " << num_outstanding_packets
    << " NumUnfinishedFlows " << num_unfinished_flows
    << " StartedFlows " << started_flows << "\n";

  if (!finished_simulation && ttl < get_current_time()) {
    add_to_event_queue(new LoggingEvent(current_time + 0.05, ttl));
  }
}

DDCHostPacketQueuingEvent::DDCHostPacketQueuingEvent(double time, Packet *packet, Queue *queue)
: PacketQueuingEvent(time, packet, queue)
{
  if(queue->unique_id == 0)
    std::cout << get_current_time() << " event.cpp:384 ddcpktqevt,cons @q " << queue->unique_id << " ptr:" << queue << "\n";
}

void DDCHostPacketQueuingEvent::process_event() {
  if (!queue->busy || ( params.preemptive_queue && this->packet->pf_priority < queue->packet_transmitting->pf_priority) ) {
    if(queue->busy && queue->queue_proc_event->unique_id == 7394)
      std::cout << get_current_time() << " event.cpp:391" << " this:" << this << " eid:" << this->unique_id << " preempting evt:" << queue->queue_proc_event->unique_id << " ptr:" << queue->queue_proc_event << "\n";
    queue->preempt_current_transmission();
    queue->queue_proc_event = new DDCHostQueueProcessingEvent(get_current_time(), queue);
    if(packet->flow->id == 0)
      std::cout << get_current_time() << " evt.cpp:387 in queuing event, flow:" << packet->flow->id << " add DDCHostQueueProcessingEvent(now)" << "\n";
    add_to_event_queue(queue->queue_proc_event);
    queue->busy = true;
    queue->packet_transmitting = this->packet;
  }
  if(packet->flow->id == 0)
    std::cout << get_current_time() << " evt.cpp:393 in queuing event, flow:" << packet->flow->id << " enqueued pkt" << "\n";
  queue->enque(packet);
}

DDCHostPacketQueuingEvent::~DDCHostPacketQueuingEvent(){}

DDCHostQueueProcessingEvent::DDCHostQueueProcessingEvent(double time, Queue *queue)
:QueueProcessingEvent(time,queue)
{
}


void DDCHostQueueProcessingEvent::process_event() {
  Packet *packet = queue->deque();
  if (packet) {
    queue->busy = true;
    queue->busy_events.clear();
    queue->packet_transmitting = packet;
    Queue *next_hop = topology->get_next_hop(packet, queue);
    double td = queue->get_transmission_delay(packet->size);
    double pd = queue->propagation_delay;
    //double additional_delay = 1e-10;
    queue->queue_proc_event = new DDCHostQueueProcessingEvent(time + td, queue);
    if(packet->flow->id == 0)
      std::cout << get_current_time() << " event.cpp:417 in DDCHostQueueProcessingEvent found pkt in queue add new DDCHostQueueProcessingEvent(" << (time + td)
      << ") " << " ptr:" << queue->queue_proc_event << " eid:" << queue->queue_proc_event->unique_id << " qid:" << queue->unique_id << "\n";
    add_to_event_queue(queue->queue_proc_event);
    queue->busy_events.push_back(queue->queue_proc_event);
    if (next_hop == NULL) {
      Event* arrival_evt = new PacketArrivalEvent(time + td + pd, packet);
      add_to_event_queue(arrival_evt);
      queue->busy_events.push_back(arrival_evt);
    } else {
      Event* queuing_evt = NULL;
      if (params.cut_through == 1) {
        double cut_through_delay = queue->get_transmission_delay(packet->flow->hdr_size);
        queuing_evt = new PacketQueuingEvent(time + cut_through_delay + pd, packet, next_hop);
      } else {
        queuing_evt = new PacketQueuingEvent(time + td + pd, packet, next_hop);
      }
      add_to_event_queue(queuing_evt);
      queue->busy_events.push_back(queuing_evt);
    }
  } else {
    if(queue->unique_id == 0)
      std::cout << get_current_time() << "event.cpp:437 in DDCHostQueueProcessingEvent no pkt in queue" << "\n";
    queue->busy = false;
    queue->busy_events.clear();
    queue->packet_transmitting = NULL;
    queue->queue_proc_event = NULL;


    while(!((Host*)(queue->src))->active_flows.empty()){
      Flow* flow = ((Host*)(queue->src))->active_flows.top();
      ((Host*)(queue->src))->active_flows.pop();
      if(!flow->finished){
        if(flow->id == 0)
          std::cout << get_current_time() << "event.cpp:437 in DDCHostQueueProcessingEvent flow sned data. fid:" << flow->id << "\n";
        flow->send_pending_data();
        break;
      }
    }
  }
}


DDCHostQueueProcessingEvent::~DDCHostQueueProcessingEvent(){}


