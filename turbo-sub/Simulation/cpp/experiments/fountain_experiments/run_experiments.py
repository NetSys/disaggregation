#!/usr/bin/python

import sys
import subprocess
import threading

conf_str = '''init_cwnd: 4
max_cwnd: 7
retx_timeout: 0.0000095
queue_size: 6200
propagation_delay: 0.0000002
bandwidth: 10000000000.0
queue_type: 2
flow_type: {0}
num_flow: {1}
flow_trace: {2}
cut_through: 0
mean_flow_size: {3}
load_balancing: 0
preemptive_queue: 0
big_switch: 0
host_type: {4}
load: {5}

'''

def get_mean_flow_size(cdf_file):
    sys.path.append("../")
    from calculate_mean_flowsize import get_mean_flowsize
    return int(get_mean_flowsize(cdf_file))

experiments = {
#        'pfabric_alllong_100k_0.6' : [2, 100000, "../CDF_alllong.txt", get_mean_flow_size("../CDF_alllong.txt"), 1, 0.6],
#        'pfabric_allshort_100k_0.6' : [2, 100000, "../CDF_allshort.txt", get_mean_flow_size("../CDF_allshort.txt"), 1, 0.6],
#        'pfabric_alllong_100k_0.8' : [2, 100000, "../CDF_alllong.txt", get_mean_flow_size("../CDF_alllong.txt"), 1, 0.8],
#        'pfabric_allshort_100k_0.8' : [2, 100000, "../CDF_allshort.txt", get_mean_flow_size("../CDF_allshort.txt"), 1, 0.8],
#        'fountain_alllong_vanilla_100k' : [100, 100000, "../CDF_alllong.txt", get_mean_flow_size("../CDF_alllong.txt"), 1, 0.8],
#        'fountain_allshort_vanilla_100k' : [100, 100000, "../CDF_allshort.txt", get_mean_flow_size("../CDF_allshort.txt"), 1, 0.8],
#        'fountain_alllong_scheduled_100k' : [101, 100000, "../CDF_alllong.txt", get_mean_flow_size("../CDF_alllong.txt"), 2, 0.8],
#        'fountain_allshort_scheduled_100k' : [101, 100000, "../CDF_allshort.txt", get_mean_flow_size("../CDF_allshort.txt"), 2, 0.8],
#        'rtscts_alllong_vanilla_100k' : [102, 100000, "../CDF_alllong.txt", get_mean_flow_size("../CDF_alllong.txt"), 3, 0.8],
#        'rtscts_allshort_vanilla_100k' : [102, 100000, "../CDF_allshort.txt", get_mean_flow_size("../CDF_allshort.txt"), 3, 0.8]
#        'fountain_alllong_pipeline_100k' : [111, 100000, "../CDF_alllong.txt", get_mean_flow_size("../CDF_alllong.txt"), 11, 0.8],
#        'fountain_allshort_pipeline_100k' : [111, 100000, "../CDF_allshort.txt", get_mean_flow_size("../CDF_allshort.txt"), 11, 0.8],
        'fountain_alllong_pipeline_100k_0.6' : [111, 100000, "../CDF_alllong.txt", get_mean_flow_size("../CDF_alllong.txt"), 11, 0.6],
#        'fountain_allshort_pipeline_100k_0.6' : [111, 100000, "../CDF_allshort.txt", get_mean_flow_size("../CDF_allshort.txt"), 11, 0.6],
#        'fountain_alllong_pipeline_100k_0.8' : [111, 100000, "../CDF_alllong.txt", get_mean_flow_size("../CDF_alllong.txt"), 11, 0.8],
#        'fountain_allshort_pipeline_100k_0.8' : [111, 100000, "../CDF_allshort.txt", get_mean_flow_size("../CDF_allshort.txt"), 11, 0.8],
}

def run_exp(exp_name):
    conf_file_str = conf_str.format(*experiments[exp_name])
    conf_file_name = 'conf_' + exp_name + '.txt'
    with open(conf_file_name, 'w') as conf_file:
        conf_file.write(conf_file_str)
    result_file_name = 'results_' + exp_name + '.txt'
    with open(result_file_name, 'w') as res_file:
        cmd = ['../../simulator', '6', conf_file_name]
        print " ".join(cmd)
        subprocess.call(cmd, stdout = res_file)

threads = []
for exp_name in experiments:
    threads.append(threading.Thread(target=run_exp, args=(exp_name,)))

[t.start() for t in threads]
[t.join() for t in threads]
print 'finished', len(threads), 'experiments'
