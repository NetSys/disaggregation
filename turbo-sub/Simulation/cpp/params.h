#ifndef PARAMS_H
#define PARAMS_H

#include <string>
#include <fstream>

struct DCExpParams {

  int initial_cwnd;
  int max_cwnd;
  double retx_timeout_value;
  int mss;
  int hdr_size;
  int queue_size;
  int queue_type;
  int flow_type;
  int load_balancing; //0 per pkt, 1 per flow

  double propagation_delay;
  double bandwidth;

  int num_flows_to_run;
  double end_time;
  std::string cdf_or_flow_trace;
  int cut_through;
  int mean_flow_size;


  int num_hosts;
  int num_agg_switches;
  int num_core_switches;
  int preemptive_queue;
  int big_switch;
  int host_type;
  double traffic_imbalance;
  double load;
  double reauth_limit;
};

void read_experiment_parameters(std::string conf_filename, uint32_t exp_type); 

/* General main function */
#define DC_EXP_WITH_TRACE 1
#define DC_EXP_WITHOUT_TRACE 2

#define DC_EXP_CONTINUOUS_FLOWMODEL 5
#define DC_EXP_UNIFORM_FLOWS 6
#define DC_EXP_UNIFORM_FLOWS_SHUFFLE_TRAFFIC 7

#define SINGLE_LINK_EXP_IONSTYLE 10
#define SINGLE_LINK_EXP_SYLVIASTYLE 11

#define N_TO_1_EXP 20

#endif
