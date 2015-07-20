#!/usr/bin/python

import os.path
import sys
sys.path.append("../")
from run_experiments import run_experiments

conf_str = '''init_cwnd: 4
max_cwnd: 7
retx_timeout: 0.0000095
queue_size: 6200
propagation_delay: 0.0000002
bandwidth: 10000000000.0
queue_type: 2
flow_type: 2
num_flow: {0}
flow_trace: {1}
cut_through: 0
mean_flow_size: {2}
load_balancing: 0
preemptive_queue: 0
big_switch: 0
host_type: 1
imbalance: {3}
load: {4}
burst_at_beginning: 1
smooth_cdf: 0
use_flow_trace: 0

'''

cdf_file = '''3 1 {0}
700 1 1
'''


def get_mean_flow_size(cdf_file):
    sys.path.append("../")
    from calculate_mean_flowsize import get_mean_flowsize
    return int(get_mean_flowsize(cdf_file))

def make_experiment(numFlow, cdf, skew, load):
    return [numFlow, cdf, get_mean_flow_size(cdf), skew, load]

def make_cdfs():
    #fracs = map(lambda x:float(x/10.0), xrange(11))
    fracs = [0.0]
    cdfs = []
    for frac in fracs:
        cdf = cdf_file.format(frac)
        name = '../CDF_{0}short.txt'.format(frac)
        if (not os.path.exists(name)):
            with open(name, 'w') as f:
                f.write(cdf)
        cdfs.append((frac,name))
    return cdfs

def cdf_experiments():
    cdfs = make_cdfs()
    numFlows = [10000]
    skew = [0]
    loads = [60]
    experiments = {}

    for n in numFlows:
        for l in loads:
            for s in skew:
                for frac, cdfFile in cdfs:
                    name = 'pfabric_{0}_{1}_skew{2}_{3}short'.format(n, l, s, frac)
                    experiments[name] = make_experiment(n, cdfFile, s, l)

    return experiments

run_experiments(conf_str, cdf_experiments())
