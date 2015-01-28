#include "factory.h"

/* Factory method to return appropriate queue */
Queue* Factory::get_queue(uint32_t id, double rate,
                        uint32_t queue_size, uint32_t type,
                        double drop_prob, int location) { // Default drop_prob is 0.0

  switch(type) {
    case DROPTAIL_QUEUE:
      return new Queue(id, rate, queue_size, location);
    case PFABRIC_QUEUE:
      return new PFabricQueue(id, rate, queue_size, location);
    case PROB_DROP_QUEUE:
      return new ProbDropQueue(id, rate, queue_size, drop_prob, location);
    case TURBO_QUEUE:
      return new TurboQueue(id, rate, queue_size, location);
  }
  assert(false);
  return NULL;
}

int Factory::flow_counter = 0;

Flow* Factory::get_flow(double start_time, uint32_t size,
                        Host *src, Host *dst, uint32_t flow_type,
                        double rate) {
  return Factory::get_flow(Factory::flow_counter++, start_time, size, src, dst, flow_type, rate);
}

Flow* Factory::get_flow(uint32_t id, double start_time, uint32_t size,
                        Host *src, Host *dst, uint32_t flow_type,
                        double rate) { // Default rate is 1.0
  switch (flow_type) {
    case NORMAL_FLOW:
      return new Flow(id, start_time, size, src, dst);
      break;
    case PFABRIC_FLOW:
      return new PFabricFlow(id, start_time, size, src, dst);
      break;
    case FULLBLAST_PACED_FLOW:
      return new FullBlastPacedFlow(id, start_time, size, src, dst);
      break;
    case PACED_FLOW:
      return new PacedFlow(id, start_time, size, src, dst, rate);
      break;
    case JITTERED_PACED_FLOW:
      return new JitteredPacedFlow(id, start_time, size, src, dst, rate);
      break;
    case TURBO_FLOW:
      return new TurboFlow(id, start_time, size, src, dst);
      break;
    case TURBO_FLOW_STOP_ON_TIMEOUT:
      return new TurboFlowStopOnTimeout(id, start_time, size, src, dst);
      break;
    case TURBO_FLOW_PERPACKET_TIMEOUT:
      return new TurboFlowPerPacketTimeout(id, start_time, size, src, dst);
      break;
    case TURBO_FLOW_LONGFLOWS_LOW:
      return new TurboFlowLongFlowsGetLowPriority(id, start_time, size, src, dst);
      break;
    case PFABRIC_FLOW_NO_SLOWSTART:
      return new PFabricFlowNoSlowStart(id, start_time, size, src, dst);
      break;
  }
  assert(false);
  return NULL;
}
