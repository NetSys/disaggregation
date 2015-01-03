
#include <iostream>
#include <algorithm>
#include <fstream>
#include <stdlib.h>
#include <deque>
#include <stdint.h>

#include "flow.h"
#include "turboflow.h"

#include "packet.h"
#include "node.h"
#include "event.h"
#include "topology.h"
#include "simpletopology.h"
#include "params.h"
#include "assert.h"
#include "queue.h"

#include "factory.h"
#include "random_variable.h"

class Experiment {
public:
  Topology *topology;
  double current_time = 0;
  double start_time = -1;
  std::priority_queue<Event *, std::vector<Event *>, EventComparator> event_queue;
  std::deque<Flow *> flows_to_schedule;
  std::deque<Event *> flow_arrivals;

  uint32_t num_outstanding_packets;
  uint32_t max_outstanding_packets;
  uint32_t duplicated_packets_received = 0;

  DCExpParams params;

  Experiment();
  ~Experiment();

  void add_to_event_queue(Event *ev);
  int get_event_queue_size();
  double get_current_time();

  void read_experiment_parameters(
    std::string conf_filename,
    uint32_t exp_type
  );

  virtual void run_scenario();
};

class PFabricExperiment {
public:
  void read_flows_to_schedule(
    std::string filename,
    uint32_t num_lines,
    PFabricTopology *topo
  );

  virtual void generate_flows_to_schedule(
    std::string filename,
    uint32_t num_flows,
    PFabricTopology *topo
  );

  void printQueueStatistics(PFabricTopology *topo);

  virtual void run_experiment(
    int argc,
    char **argv,
    uint32_t exp_type
  );
};

class ContinuousModelExperiment : PFabricExperiment {
public:
  double end_time;

  virtual void generate_flows_to_schedule(
    std::string filename,
    uint32_t num_flows,
    PFabricTopology *topo
  );

  virtual void run_experiment(
    int argc,
    char **argv,
    uint32_t exp_type
  );

  virtual void run_scenario();
};

class FixedDistributionExperiment : PFabricExperiment {
public:
  virtual void generate_flows_to_schedule(
    std::string filename,
    uint32_t num_flows,
    PFabricTopology *topo
  );
};
