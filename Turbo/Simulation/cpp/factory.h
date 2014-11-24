#ifndef FACTORY_H
#define FACTORY_H

#include "flow.h"
#include "queue.h"
#include "pacedflow.h"
#include "turboflow.h"
#include "turboqueue.h"

/* Queue types */
#define DROPTAIL_QUEUE 1
#define PFABRIC_QUEUE 2
#define TURBO_QUEUE 3
#define PROB_DROP_QUEUE 4

/* Flow types */
#define NORMAL_FLOW 1
#define PFABRIC_FLOW 2
#define FULLBLAST_PACED_FLOW 3
#define PACED_FLOW 7
#define JITTERED_PACED_FLOW 8
#define TURBO_FLOW 4
#define TURBO_FLOW_STOP_ON_TIMEOUT 5
#define TURBO_FLOW_PER_PKT_TIMEOUT 6

class Factory {
public:
  static Flow *get_flow(uint32_t id, double start_time, uint32_t size,
                        Host *src, Host *dst, uint32_t flow_type,
                        double paced_rate = 0.0);
  static Queue *get_queue(uint32_t id, double rate,
                          uint32_t queue_size, uint32_t type,
                          double drop_prob = 0);
};

#endif
