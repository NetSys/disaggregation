#ifndef PARAMS_H
#define PARAMS_H

#include <string>

struct DCExpParams {
  int initial_cwnd;
  int max_cwnd;
  double retx_timeout_value;
  int mss;
  int hdr_size;
  int queue_size;
  int queue_type;
  int flow_type;

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
};

/* General main function */
#define DC_EXP_WITH_TRACE 1
#define DC_EXP_WITHOUT_TRACE 2

#define DC_EXP_CONTINUOUS_FLOWMODEL 5
#define DC_EXP_UNIFORM_FLOWS 6

#define SINGLE_LINK_EXP_IONSTYLE 10
#define SINGLE_LINK_EXP_SYLVIASTYLE 11

#define N_TO_1_EXP 20

#endif
