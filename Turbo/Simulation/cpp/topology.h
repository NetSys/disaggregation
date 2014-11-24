#ifndef TOPOLOGY_H
#define TOPOLOGY_H


#include "node.h"
#include "assert.h"
#include "params.h"
#include "factory.h"
#include "packet.h"
#include "queue.h"
#include <cstddef>
#include <iostream>
#include <math.h>
#include <vector>

class Topology {
public:
  Topology();
  virtual Queue *get_next_hop(Packet *p, Queue *q) = 0;
  virtual double get_oracle_fct(Flow* f) = 0;
};

class PFabricTopology : public Topology {
public:
  PFabricTopology(uint32_t num_hosts, uint32_t num_agg_switches,
    uint32_t num_core_switches, double bandwidth, uint32_t queue_type);
  virtual Queue *get_next_hop(Packet *p, Queue *q);
  virtual double get_oracle_fct(Flow* f);

  std::vector<Host *> hosts;
  std::vector<AggSwitch *> agg_switches;
  std::vector<CoreSwitch *> core_switches;
};

class CutThroughTopology : public PFabricTopology {
public:
  CutThroughTopology(uint32_t num_hosts, uint32_t num_agg_switches,
    uint32_t num_core_switches, double bandwidth, uint32_t queue_type);
  virtual double get_oracle_fct(Flow* f);

};




#endif
