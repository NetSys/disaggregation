#ifndef PARAMS_H
#define PARAMS_H

#include <string>
#include <fstream>

struct DCExpParams {
  std::string param_str;

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

  double magic_trans_slack;
  int magic_delay_scheduling;

  int use_flow_trace;
  int smooth_cdf;
  int burst_at_beginning;
  double capability_timeout;
  double capability_resend_timeout;
  int capability_initial;
  int capability_window;
  double capability_window_timeout;

  int ddc;
  double ddc_cpu_ratio;
  double ddc_mem_ratio;
  double ddc_disk_ratio;


};


#define CAPABILITY_MEASURE_WASTE false
#define CAPABILITY_FOURTH_LEVEL false
#define CAPABILITY_NOTIFY_BLOCKING false

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

#define INFINITESIMAL_TIME 0.000000000001

#endif
