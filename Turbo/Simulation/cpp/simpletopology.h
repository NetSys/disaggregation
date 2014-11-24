#ifndef SIMPLE_TOPOLOGY_H
#define SIMPLE_TOPOLOGY_H

#include "topology.h"

class SingleLinkTopology : public Topology {
public:
  SingleLinkTopology(double bandwidth, double drop_prob);
  virtual Queue *get_next_hop(Packet *p, Queue *q);
  virtual double get_oracle_fct(Flow* f);

  Host *src;
  Host *dst;
};


class SingleSenderReceiverTopology : public Topology {
public:
  SingleSenderReceiverTopology(double bandwidth, double drop_prob);
  virtual Queue *get_next_hop(Packet *p, Queue *q);
  virtual double get_oracle_fct(Flow* f);

  Host *src;
  CoreSwitch *sw;
  Host *dst;
};



class NToOneTopology : public Topology {
public:
  NToOneTopology(uint32_t num_senders, double bandwidth);
  virtual Queue *get_next_hop(Packet *p, Queue *q);
  virtual double get_oracle_fct(Flow* f);

  uint32_t num_senders;
  std::vector<Host *> senders;
  Host *receiver;
  CoreSwitch *sw;
};

#endif
