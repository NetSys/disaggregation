
#include <iostream>
#include <algorithm>
#include <fstream>
#include <stdlib.h>
#include <deque>
#include <stdint.h>
#include <iomanip>

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


extern void run_scenario();
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

/* pFabric Experiments */
/* Reads flow information from an input trace */
void read_flows_to_schedule(std::string filename, uint32_t num_lines,
                           Topology *topo) {
  std::ifstream input(filename);
  while(!input.eof()) {
    double start_time, temp;
    uint32_t size, s, d;
    uint32_t id;
    if((input >> id).eof())
        break;
    input >> start_time;
    input >> temp;
    input >> temp; size = (uint32_t) (params.mss * temp);
    input >> temp; input >> temp;
    input >> s >> d;

    //std::cout << "Flow " << id << " " << start_time << " " << size << " " << s << " " << d << "\n";

    flows_to_schedule.push_back(Factory::get_flow(id, start_time, size,
      topo->hosts[s], topo->hosts[d], params.flow_type));
    if(flows_to_schedule.size() % 10000000 == 0)
        std::cout << "Loaded " << flows_to_schedule.size() << " flows\n";
  }
  params.num_flows_to_run = flows_to_schedule.size();
  input.close();
}

/* Generates flow information from a cdf */
void generate_flows_to_schedule(std::string filename, uint32_t num_flows,
                                PFabricTopology *topo) {
  //double lambda = 4.0966649051007566;
  double lambda = params.bandwidth * params.load /
                  (params.mean_flow_size * 8.0 / 1460 * 1500);
  double lambda_per_host = lambda / (topo->hosts.size() - 1);
  std::cout << "Lambda: " << lambda_per_host << std::endl;

  EmpiricalRandomVariable *nv_bytes =  new EmpiricalRandomVariable(filename);
  ExponentialRandomVariable *nv_intarr = new ExponentialRandomVariable(1.0 / lambda_per_host);
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


void printQueueStatistics(Topology *topo) {
    double totalSentFromHosts = 0;

    uint64_t dropAt[4];
    uint64_t total_drop = 0;
    for (auto i = 0; i < 4; i++) {
        dropAt[i] = 0;
    }

    for (auto i = 0; i < topo->hosts.size(); i++) {
        int location = topo->hosts[i]->queue->location;
        dropAt[location] += topo->hosts[i]->queue->pkt_drop;
    }


    for (uint i = 0; i < topo->switches.size(); i++) {
        for (uint j = 0; j < topo->switches[i]->queues.size(); j++) {
            int location = topo->switches[i]->queues[j]->location;
            dropAt[location] += topo->switches[i]->queues[j]->pkt_drop;
        }
    }

    for (int i = 0; i < 4; i++) {
        total_drop += dropAt[i];
    }
    for (int i = 0; i < 4; i++) {
        std::cout << "Hop:" << i << " Drp:" << dropAt[i] << "("  << (int)((double)dropAt[i]/total_drop * 100) << "%) ";
    }

    for (auto h = (topo->hosts).begin(); h != (topo->hosts).end(); h++) {
        totalSentFromHosts += (*h)->queue->b_departures;
    }

    std::cout << " Overall:" << std::setprecision(2) <<(double)total_drop*1460/totalSentFromHosts << "\n";

    double totalSentToHosts = 0;
    int drop_ss = 0, drop_sl = 0, drop_ll = 0;
    for (auto tor = (topo->switches).begin(); tor != (topo->switches).end(); tor++) {
        for (auto q = ((*tor)->queues).begin(); q != ((*tor)->queues).end(); q++) {
            if ((*q)->rate == params.bandwidth) totalSentToHosts += (*q)->b_departures;
        }
    }

    double dead_bytes = totalSentFromHosts - totalSentToHosts;
    double total_bytes = 0;
    for (auto f = flows_to_schedule.begin(); f != flows_to_schedule.end(); f++) {
        total_bytes += (*f)->size;
    }

    double simulation_time = current_time - start_time;
    double utilization = (totalSentFromHosts * 8.0 / 144.0) / simulation_time;
    double dst_utilization = (totalSentToHosts * 8.0 / 144.0) / simulation_time;

    std::cout 
        << "DeadPackets " << 100.0 * (dead_bytes/total_bytes)
        << "% DuplicatedPackets " << 100.0 * duplicated_packets_received * 1460.0 / total_bytes
        << "% Utilization " << utilization / 10000000000 * 100 << "% " << dst_utilization / 10000000000 * 100  << "%\n";
}


void run_pFabric_experiment(int argc, char **argv, uint32_t exp_type) {
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
  if (exp_type == DC_EXP_WITH_TRACE) {
    read_flows_to_schedule(params.cdf_or_flow_trace, num_flows, topo);
  } else if (exp_type == DC_EXP_WITHOUT_TRACE) {
    generate_flows_to_schedule(params.cdf_or_flow_trace, num_flows, topo);
  }
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
  double sum = 0, sum_norm = 0;
  for (uint32_t i = 0; i < flows_sorted.size(); i++) {
    Flow *f = flows_to_schedule[i];
    sum += 1000000.0 * f->flow_completion_time;
    sum_norm += 1000000.0 * f->flow_completion_time /
                topology->get_oracle_fct(f);
  }
  std::cout << "AverageFCT " << sum / flows_sorted.size() <<
    " MeanSlowdown " << sum_norm / flows_sorted.size() << "\n";
  printQueueStatistics(topo);
}

