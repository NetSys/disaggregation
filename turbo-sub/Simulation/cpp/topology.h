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

class FastpassArbiter;

class Topology {
public:
  Topology();
  virtual Queue *get_next_hop(Packet *p, Queue *q) = 0;
  virtual double get_oracle_fct(Flow* f) = 0;

  uint32_t num_hosts;

  std::vector<Host *> hosts;
  std::vector<Switch*> switches;

  FastpassArbiter* arbiter;
};

class PFabricTopology : public Topology {
public:
  PFabricTopology(uint32_t num_hosts, uint32_t num_agg_switches,
    uint32_t num_core_switches, double bandwidth, uint32_t queue_type);
  virtual Queue *get_next_hop(Packet *p, Queue *q);
  virtual double get_oracle_fct(Flow* f);


  uint32_t num_agg_switches;
  uint32_t num_core_switches;


  std::vector<AggSwitch *> agg_switches;
  std::vector<CoreSwitch *> core_switches;

};


class BigSwitchTopology : public Topology {
public:
  BigSwitchTopology(uint32_t num_hosts, double bandwidth, uint32_t queue_type);
  virtual Queue *get_next_hop(Packet *p, Queue *q);
  virtual double get_oracle_fct(Flow* f);


  CoreSwitch* the_switch;

};

class CutThroughTopology : public PFabricTopology {
public:
  CutThroughTopology(uint32_t num_hosts, uint32_t num_agg_switches,
    uint32_t num_core_switches, double bandwidth, uint32_t queue_type);
  virtual double get_oracle_fct(Flow* f);

};




#endif
