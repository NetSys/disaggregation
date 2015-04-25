#!/usr/bin/python

import sys
import subprocess
import threading
import os

os.system("cd ../..;make;cd -")

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
traffic_imbalance: {5}
load: {6}
reauth_limit: 3
use_flow_trace: 0
smooth_cdf: {7}
burst_at_beginning: 0
'''

def get_mean_flow_size(cdf_file):
    sys.path.append("../")
    from calculate_mean_flowsize import get_mean_flowsize
    return int(get_mean_flowsize(cdf_file))

experiments = {}

schemes = {
	"pfabric" : [2, 1],
	"capability-prio-turbo" : [112, 12],
}
nflow = [100]
load = [0.6, 0.8]
fsize = ["00short", "10short", "20short", "30short", "40short", "50short", "60short", "70short", "80short", "90short", "allshort"]
#fsize = ["aditya", "dctcp", "datamining"]
skew =  [0.0]
smooth = 0

for sh in schemes:
	for l in load:
	    for f in fsize:
	        for s in skew:
	        	for nf in nflow:
		            key = sh + '_' + f + '_load' + str(l) + '_skew' + str(s) + '_' + str(nf) + 'k'
		            value = [schemes[sh][0], nf * 1000, "../CDF_" + f + ".txt", get_mean_flow_size("../CDF_" + f + ".txt"), schemes[sh][1], s, l, smooth]
		            experiments[key] = value
    

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