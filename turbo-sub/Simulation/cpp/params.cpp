#include "params.h"

DCExpParams params;

/* Read parameters from a config file */
void read_experiment_parameters(std::string conf_filename, uint32_t exp_type) {
    std::ifstream input(conf_filename);

    std::string temp;
    input >> temp; input >> params.initial_cwnd;
    input >> temp; input >> params.max_cwnd;
    input >> temp; input >> params.retx_timeout_value;
    input >> temp; input >> params.queue_size;
    input >> temp; input >> params.propagation_delay;
    input >> temp; input >> params.bandwidth;
    input >> temp; input >> params.queue_type;
    input >> temp; input >> params.flow_type;

    input >> temp;
    if (exp_type == DC_EXP_CONTINUOUS_FLOWMODEL) {
        input >> params.end_time;
    }
    else {
        input >> params.num_flows_to_run;
    }

    input >> temp; input >> params.cdf_or_flow_trace;
    input >> temp; input >> params.cut_through;
    input >> temp; input >> params.mean_flow_size;
    input >> temp; input >> params.load_balancing;
    input >> temp; input >> params.preemptive_queue;
    input >> temp; input >> params.big_switch;
    input >> temp; input >> params.host_type;
    input >> temp; input >> params.traffic_imbalance;
    input >> temp; input >> params.load;

    params.hdr_size = 40;
    params.mss = 1460;
}
