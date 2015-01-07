
#include <iostream>
#include <algorithm>
#include <fstream>
#include <stdlib.h>
#include <deque>
#include <stdint.h>
#include <cstdlib>
#include <ctime>

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

extern void printQueueStatistics(PFabricTopology *topo);
extern void run_scenario();

void generate_flows_to_schedule_fd(std::string filename, uint32_t num_flows,
PFabricTopology *topo) {
  //double lambda = 4.0966649051007566;
  double lambda = params.bandwidth * 0.8 /
  (params.mean_flow_size * 8.0 / 1460 * 1500);
  double lambda_per_host = lambda / (topo->hosts.size() - 1);
  std::cout << "Lambda: " << lambda_per_host << std::endl;

  //use an NAryRandomVariable for true uniform/bimodal/trimodal/etc
  // EmpiricalRandomVariable *nv_bytes =
  // new NAryRandomVariable(filename);
  EmpiricalRandomVariable *nv_bytes =
    new CDFRandomVariable(filename);

  ExponentialRandomVariable *nv_intarr =
    new ExponentialRandomVariable(1.0 / lambda_per_host);
  //* [expr ($link_rate*$load*1000000000)/($meanFlowSize*8.0/1460*1500)]
  for (uint32_t i = 0; i < topo->hosts.size(); i++) {
    for (uint32_t j = 0; j < topo->hosts.size(); j++) {
      if (i != j) {
        double first_flow_time = 1.0 + nv_intarr->value();
        add_to_event_queue(
        new FlowCreationForInitializationEvent(first_flow_time,
        topo->hosts[i], topo->hosts[j],
        nv_bytes, nv_intarr));
      }
    }
  }
  while (event_queue.size() > 0) {
    Event *ev = event_queue.top();
    event_queue.pop();
    current_time = ev->time;
    if (flows_to_schedule.size() < num_flows) {
      ev->process_event();
    }
    delete ev;
  }
  current_time = 0;
}


//same as run_pFabric_experiment except with this generate_flows.
void run_fixedDistribution_experiment(int argc, char **argv, uint32_t exp_type) {
  if (argc < 3) {
    std::cout << "Usage: <exe> exp_type conf_file" << std::endl;
    return;
  }
  std::string conf_filename(argv[2]);
  read_experiment_parameters(conf_filename, exp_type);
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

  uint32_t num_flows = params.num_flows_to_run;

  //no reading flows to schedule in this mode.
  generate_flows_to_schedule_fd(params.cdf_or_flow_trace, num_flows, topo);

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

  std::cout << "Running " << num_flows << " Flows\nCDF_File " <<
    params.cdf_or_flow_trace << "\nBandwidth " << params.bandwidth/1e9 <<
    "\nQueueSize " << params.queue_size <<
    "\nCutThrough " << params.cut_through <<
    "\nFlowType " << params.flow_type <<
    "\nQueueType " << params.queue_type <<
    "\nInit CWND " << params.initial_cwnd <<
    "\nMax CWND " << params.max_cwnd <<
    "\nRtx Timeout " << params.retx_timeout_value  <<
    "\nload_balancing (0: pkt)" << params.load_balancing <<
    std::endl;

  run_scenario();
  // print statistics
  double sum = 0, sum_norm = 0, sum_inflation = 0;
  for (uint32_t i = 0; i < flows_sorted.size(); i++) {
    Flow *f = flows_to_schedule[i];
    sum += 1000000.0 * f->flow_completion_time;
    sum_norm += 1000000.0 * f->flow_completion_time /
      topology->get_oracle_fct(f);
    sum_inflation += (double)f->total_pkt_sent / (f->size/f->mss);
  }
  std::cout << "AverageFCT " << sum / flows_sorted.size() <<
  " MeanSlowdown " << sum_norm / flows_sorted.size() <<
  " MeanInflation " << sum_inflation / flows_sorted.size() <<
  "\n";
  printQueueStatistics(topo);
}














/* Runs a initialized scenario */
void run_scenario_shuffle_traffic() {
  // Flow Arrivals create new flow arrivals
  // Add the first flow arrival

  while (event_queue.size() > 0) {
    Event *ev = event_queue.top();
    event_queue.pop();
    current_time = ev->time;
    if (start_time < 0) {
      start_time = current_time;
    }
    //event_queue.pop();
    //std::cout << "main.cpp::run_scenario():" << get_current_time() << " Processing " << ev->type << " " << event_queue.size() << std::endl;
    if (ev->cancelled) {
      delete ev; //TODO: Smarter
      continue;
    }
    ev->process_event();
    delete ev;
  }
}





//same as run_pFabric_experiment except with this generate_flows.
void run_fixedDistribution_experiment_shuffle_traffic(int argc, char **argv, uint32_t exp_type) {
  std::cout << "run_fixedDistribution_experiment_shuffle_traffic\n";
  if (argc < 3) {
    std::cout << "Usage: <exe> exp_type conf_file" << std::endl;
    return;
  }
  std::string conf_filename(argv[2]);
  read_experiment_parameters(conf_filename, exp_type);
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




//
//  uint32_t num_flows = params.num_flows_to_run;
//
//  //no reading flows to schedule in this mode.
//  generate_flows_to_schedule_fd(params.cdf_or_flow_trace, num_flows, topo);
//
//  std::deque<Flow *> flows_sorted = flows_to_schedule;
//  struct FlowComparator {
//    bool operator() (Flow *a, Flow *b) {
//      return a->start_time < b->start_time;
//    }
//  } fc;
//  std::sort (flows_sorted.begin(), flows_sorted.end(), fc);
//
//  for(uint32_t i = 0; i < flows_sorted.size(); i++) {
//    Flow *f = flows_sorted[i];
//    flow_arrivals.push_back(new FlowArrivalEvent(f->start_time, f));
//  }


  int traffic_matrix[144];
  for(int i = 0; i < 144; i++)
    traffic_matrix[i] = i;

  for(int i = 0; i < 144; i++){
    int j = std::rand()%(i+1);
    int s = traffic_matrix[i];
    traffic_matrix[i] = traffic_matrix[j];
    traffic_matrix[j] = s;
  }

  for(int i = 0; i < 144; i++){
    Host* src = topo->hosts[i];
    Host* dst = topo->hosts[traffic_matrix[i]];
    uint size = 3 * 1460;
    Flow* flow = Factory::get_flow(1, size, src, dst, params.flow_type);
    flow->useDDCTestFlowFinishedEvent = true;
    flows_to_schedule.push_back(flow);
    Event * event = new FlowArrivalEvent(flow->start_time, flow);
    add_to_event_queue(event);
  }




  add_to_event_queue(new LoggingEvent(1 + 0.01));

  std::cout << "Running " << params.num_flows_to_run << " Flows\nCDF_File " <<
    params.cdf_or_flow_trace << "\nBandwidth " << params.bandwidth/1e9 <<
    "\nQueueSize " << params.queue_size <<
    "\nCutThrough " << params.cut_through <<
    "\nFlowType " << params.flow_type <<
    "\nQueueType " << params.queue_type <<
    "\nInit CWND " << params.initial_cwnd <<
    "\nMax CWND " << params.max_cwnd <<
    "\nRtx Timeout " << params.retx_timeout_value  <<
    "\nload_balancing (0: pkt)" << params.load_balancing <<
    std::endl;

  run_scenario_shuffle_traffic();

  std::deque<Flow *> flows_sorted = flows_to_schedule;
  struct FlowComparator {
    bool operator() (Flow *a, Flow *b) {
      return a->start_time < b->start_time;
    }
  } fc;
  std::sort(flows_sorted.begin(), flows_sorted.end(), fc);

  // print statistics
  double sum = 0, sum_norm = 0, sum_inflation = 0;
  for (uint32_t i = 0; i < flows_sorted.size(); i++) {
    Flow *f = flows_to_schedule[i];
    sum += 1000000.0 * f->flow_completion_time;
    sum_norm += 1000000.0 * f->flow_completion_time /
      topology->get_oracle_fct(f);
    sum_inflation += (double)f->total_pkt_sent / (f->size/f->mss);
  }
  std::cout << "AverageFCT " << sum / flows_sorted.size() <<
  " MeanSlowdown " << sum_norm / flows_sorted.size() <<
  " MeanInflation " << sum_inflation / flows_sorted.size() <<
  "\n";
  printQueueStatistics(topo);
}
