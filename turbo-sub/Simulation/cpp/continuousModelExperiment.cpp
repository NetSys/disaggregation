
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

extern Topology *topology;
extern double current_time;
extern std::priority_queue<Event *, std::vector<Event *>, EventComparator> event_queue;
extern std::deque<Flow *> flows_to_schedule;
extern std::deque<Event *> flow_arrivals;

extern uint32_t num_outstanding_packets;
extern uint32_t max_outstanding_packets;
extern DCExpParams params;
extern void add_to_event_queue(Event *);
extern void read_experiment_parameters(std::string conf_filename, uint32_t exp_type);
extern uint32_t duplicated_packets_received;

extern double start_time;

extern void printQueueStatistics(Topology *topo);

// Runs a initialized scenario
// Special version for continuous flow model that checks end time
void run_continuous_scenario(double end_time) {
  // Flow Arrivals create new flow arrivals
  // Add the first flow arrival
  if (flow_arrivals.size() > 0) {
    add_to_event_queue(flow_arrivals.front());
    flow_arrivals.pop_front();
  }
  while (event_queue.size() > 0) {
    Event *ev = event_queue.top();
    if (ev->time > end_time) {
      //stop the experiment
      break;
    }
    event_queue.pop();
    current_time = ev->time;
    if (start_time < 0) {
      start_time = current_time;
    }
    //event_queue.pop();    //std::cout << get_current_time() << " Processing " << ev->type << " " << event_queue.size() << std::endl;
    if (ev->cancelled) {
      delete ev; //TODO: Smarter
      continue;
    }
    ev->process_event();
    delete ev;
  }
}

/* Generates flow information from a cdf */
void generate_flows_to_schedule(std::string filename, double end_time,
                                PFabricTopology *topo) {
  //double lambda = 4.0966649051007566;
  double lambda = params.bandwidth * 0.8 /
                  (params.mean_flow_size * 8.0 / 1460 * 1500);
  double lambda_per_host = lambda / (topo->hosts.size() - 1);
  std::cout << "Lambda: " << lambda_per_host << std::endl;

  EmpiricalRandomVariable *nv_bytes =
    new EmpiricalRandomVariable(filename);
  ExponentialRandomVariable *nv_intarr =
    new ExponentialRandomVariable(1.0 / lambda_per_host);

  //* [expr ($link_rate*$load*1000000000)/($meanFlowSize*8.0/1460*1500)]
  // schedule the first flow between each pair of hosts
  for (uint32_t i = 0; i < topo->hosts.size(); i++) {
    for (uint32_t j = 0; j < topo->hosts.size(); j++) {
      if (i != j) {
        double first_flow_time = 1.0 + nv_intarr->value();
        add_to_event_queue(
          new FlowCreationForInitializationEventWithTimeLimit(
            end_time,
            first_flow_time,
            topo->hosts[i],
            topo->hosts[j],
            nv_bytes,
            nv_intarr
          )
        );
      }
    }
  }
  // process the flow creation events, which add any additional flows
  while (event_queue.size() > 0) {
    Event *ev = event_queue.top();
    event_queue.pop();
    current_time = ev->time;
    if (current_time < end_time) {
      ev->process_event();
    }
    delete ev;
  }
  current_time = 0;
}

void run_continuous_experiment(int argc, char **argv) {
  if (argc < 3) {
    std::cout << "Usage: <exe> exp_type conf_file" << std::endl;
    return;
  }
  std::string conf_filename(argv[2]);
  read_experiment_parameters(conf_filename, DC_EXP_CONTINUOUS_FLOWMODEL);
  params.num_hosts = 144;
  params.num_agg_switches = 9;
  params.num_core_switches = 4;


  if (params.cut_through == 1) {
    topology = new CutThroughTopology(params.num_hosts, params.num_agg_switches,
      params.num_core_switches, params.bandwidth, params.queue_type);
  } else {
    topology = new PFabricTopology(params.num_hosts, params.num_agg_switches,
      params.num_core_switches, params.bandwidth, params.queue_type);
  }

  PFabricTopology *topo = (PFabricTopology *) topology;

  //use the num_flows parameter for the end time.
  double end_time = params.end_time;
  std::cout << "end time: " << end_time << std::endl;
  //generation only for continuous model. no read from trace.
  generate_flows_to_schedule(params.cdf_or_flow_trace, end_time, topo);
  std::deque<Flow *> flows_sorted = flows_to_schedule;
  struct FlowComparator {
    bool operator() (Flow *a, Flow *b) {
      return a->start_time < b->start_time;
    }
  } fc;
  std::sort (flows_sorted.begin(), flows_sorted.end(), fc);

  for(uint32_t i = 0; i < flows_sorted.size(); i++) {
    Flow *f = flows_sorted[i];
    flow_arrivals.push_back(new FlowArrivalEvent(f->start_time, f));
  }

  add_to_event_queue(new LoggingEvent((flows_sorted.front())->start_time + 0.01));

  std::cout
    << "Running Until time " << end_time
    << "\nCDF_File " << params.cdf_or_flow_trace
    << "\nBandwidth " << params.bandwidth/1e9
    << "\nQueueSize " << params.queue_size
    << "\nCutThrough " << params.cut_through
    << "\nFlowType " << params.flow_type
    << "\nQueueType " << params.queue_type
    << "\nInit CWND " << params.initial_cwnd
    << "\nMax CWND " << params.max_cwnd
    << "\nRtx Timeout " << params.retx_timeout_value
    << std::endl;

  run_continuous_scenario(end_time);
  // print statistics
  double sum = 0, sum_norm = 0;
  uint32_t num_finished_flows = 0;
  double unfinished_flows_size = 0;
  for (uint32_t i = 0; i < flows_sorted.size(); i++) {
    Flow *f = flows_sorted[i];
    if (f->finished != 0) {
      num_finished_flows ++;
      sum += 1000000.0 * f->flow_completion_time;
      sum_norm += 1000000.0 * f->flow_completion_time /
                topology->get_oracle_fct(f);
    }
    else {
      std::cout
        << "Unfinished "
        << f->id << " "
        << f->size << " "
        << f->src->id << " "
        << f->dst->id << " "
        << f->start_time << " "
        << std::endl;
      unfinished_flows_size += f->size;
    }
  }
  uint32_t num_unfinished_flows = flows_sorted.size() - num_finished_flows;
  std::cout
    << "AverageFCT " << sum / num_finished_flows
    << " MeanSlowdown " << sum_norm / num_finished_flows
    << std::endl;
  std::cout
    << "Num Unfinished Flows " << num_unfinished_flows
    << " Average Unifinished Flow Size " << unfinished_flows_size / num_unfinished_flows
    << std::endl;
  printQueueStatistics(topo);
}
