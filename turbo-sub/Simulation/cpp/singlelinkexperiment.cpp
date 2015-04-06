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
#include "pacedflow.h"
#include "factory.h"
#include "random_variable.h"

extern void read_experiment_parameters(std::string conf_filename, uint32_t exp_type);
extern void run_scenario();
extern Topology *topology;
extern double current_time;
extern std::deque<Flow *> flows_to_schedule;
extern std::deque<Event *> flow_arrivals;

extern uint32_t num_outstanding_packets;
extern uint32_t max_outstanding_packets;
extern DCExpParams params;


/* Single Link Experiments */
void initialize_single_link_experiment(int flow_size, double drop_prob) {
  current_time = 0;
  flows_to_schedule.clear();
  //cout <<" Bandwidth:" << BANDWIDTH << "\n";
  topology = new SingleLinkTopology(params.bandwidth, drop_prob);
  SingleLinkTopology *topo = (SingleLinkTopology *) topology;
  /* Create the flows and arrivals */
  flows_to_schedule.push_back(new FullBlastPacedFlow(0, 0.0, flow_size,
    topo->src, topo->dst));
  for(uint32_t i = 0; i < flows_to_schedule.size(); i++) {
    Flow *f = flows_to_schedule[i];
    flow_arrivals.push_back(new FlowArrivalEvent(f->start_time, f));
  }
}

void run_single_link_experiment(int argc, char ** argv) {
  if (argc < 6) {
    std::cout << "Usage: <exe> exp_type conf_file flow_size \
      drop_probability num_runs" << std::endl;
    return;
  }
  read_experiment_parameters(std::string(argv[2]), SINGLE_LINK_EXP_IONSTYLE);
  int flow_size = atoi(argv[3]) * params.mss;
  double drop_prob = atof(argv[4]);
  int num_runs = atoi(argv[5]);

  for (int i = 0; i < num_runs; i++) {
    initialize_single_link_experiment(flow_size, drop_prob);
    run_scenario();
    Flow *f = flows_to_schedule[0];
    double fct = 1000000.0 * f->flow_completion_time;
    double oracle_fct = topology->get_oracle_fct(f);
    std::cout << f->size / params.mss << " ";
    std::cout << fct << " " << oracle_fct;
    std::cout << " " << fct / oracle_fct << "\n";
  }
}




/* Single Sender Receiver Experiments */
void initialize_single_sender_receiver_exp(int flow_size, double drop_prob) {
  current_time = 0;
  flows_to_schedule.clear();
  //cout <<" Bandwidth:" << BANDWIDTH << "\n";
  topology = new SingleSenderReceiverTopology(params.bandwidth, drop_prob);
  SingleSenderReceiverTopology *topo =
    (SingleSenderReceiverTopology *) topology;

  /* Create the flows and arrivals */
  flows_to_schedule.push_back(new FullBlastPacedFlow(0, 0.0, flow_size,
    topo->src, topo->dst));
  for(uint32_t i = 0; i < flows_to_schedule.size(); i++) {
    Flow *f = flows_to_schedule[i];
    flow_arrivals.push_back(new FlowArrivalEvent(f->start_time, f));
  }
}

void run_single_sender_receiver_exp(int argc, char ** argv) {
  if (argc < 6) {
    std::cout << "Usage: <exe> exp_type conf_file flow_size \
      drop_probability num_runs" << std::endl;
    return;
  }
  read_experiment_parameters(std::string(argv[2]), SINGLE_LINK_EXP_SYLVIASTYLE);
  int flow_size = atoi(argv[3]) * params.mss;
  double drop_prob = atof(argv[4]);
  int num_runs = atoi(argv[5]);
  for (int i = 0; i < num_runs; i++) {
    initialize_single_sender_receiver_exp(flow_size, drop_prob);
    run_scenario();

    Flow *f = flows_to_schedule[0];
    double fct = 1000000.0 * f->flow_completion_time;
    double oracle_fct = topology->get_oracle_fct(f);
    std::cout << f->size / params.mss << " ";
    std::cout << fct << " " << oracle_fct;
    std::cout << " " << fct / oracle_fct << "\n";
  }
}


void calculateDeadPackets_nto1(NToOneTopology *t) {
  //dead packets = bytes sent by hosts divided by bytes received at receiver
  double bytes_sent = 0;
  for (uint32_t i = 0;i<t->num_senders;i++) {
    Host *h = t->senders[i];
    bytes_sent += h->queue->b_departures;
  }
  double bytes_received = 0;
  for (uint32_t i = 0;i<t->sw->queues.size();i++) {
    Queue *q = t->sw->queues[i];
    if (q->interested) bytes_received += q->b_departures;
  }
  std::cout << "Dead Packets " << bytes_sent << " " << bytes_received << " " << 100*((bytes_sent-bytes_received)/bytes_received) << "\n";
}

/* N to 1 Experiments */
void initialize_nto1_experiment(uint32_t flow_size, uint32_t num_senders) {
  current_time = 0;
  flows_to_schedule.clear();
  topology = new NToOneTopology(num_senders, params.bandwidth);
  NToOneTopology *topo = (NToOneTopology *) topology;
  for (uint32_t i = 0; i < num_senders; i++) {
    if (params.flow_type == JITTERED_PACED_FLOW ||
      params.flow_type == PACED_FLOW) {
      flows_to_schedule.push_back(Factory::get_flow(i, 0, flow_size,
        topo->senders[i], topo->receiver, params.flow_type, 1.0 / num_senders));
    } else {
      flows_to_schedule.push_back(Factory::get_flow(i, i*1e-9,
        (i+4) * params.mss, topo->senders[i], topo->receiver,
        params.flow_type));
    }
  }
  for(uint32_t i = 0; i < flows_to_schedule.size(); i++) {
    Flow *f = flows_to_schedule[i];
    flow_arrivals.push_back(new FlowArrivalEvent(f->start_time, f));
  }
}



void run_nto1_experiment(int argc, char ** argv) {
  if (argc < 5) {
    std::cout << "Usage: <exe> exp_type conf_file flow_size num_senders"
      << std::endl;
    return;
  }
  read_experiment_parameters(std::string(argv[2]), N_TO_1_EXP);
  uint32_t flow_size = atoi(argv[3]) * params.mss;
  uint32_t num_senders = atoi(argv[4]);

  std::cout << "Running " << num_senders << " Flows\nCDF_File " <<
    params.cdf_or_flow_trace << "\nBandwidth " << params.bandwidth/1e9 <<
    "\nQueueSize " << params.queue_size <<
    "\nCutThrough " << params.cut_through <<
    "\nFlowType " << params.flow_type <<
    "\nQueueType " << params.queue_type <<
    "\nInit CWND " << params.initial_cwnd <<
    "\nMax CWND " << params.max_cwnd <<
    "\nRtx Timeout " << params.retx_timeout_value << std::endl;

  initialize_nto1_experiment(flow_size, num_senders);
  run_scenario();

  double sum = 0, sum_norm = 0;
  for (uint32_t i = 0; i < flows_to_schedule.size(); i++) {
    Flow *f = flows_to_schedule[i];
    sum += 1000000.0 * f->flow_completion_time;
    sum_norm += 1000000.0 * f->flow_completion_time /
                topology->get_oracle_fct(f);
  }
  std::cout << "AverageFCT " << sum / flows_to_schedule.size() <<
    " MeanSlowdown " << sum_norm / flows_to_schedule.size() << "\n";

  calculateDeadPackets_nto1((NToOneTopology*) topology);
}
