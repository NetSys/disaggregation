#!/usr/bin/python

from __future__ import division
import re
import sys

'''
Analyze the unfinished flows for a continuous flow model experiment.
'''

if (len(sys.argv) != 2):
    print('usage: python analyze_unfinished_flows.py <flow trace>')

flow_trace = sys.argv[1]

def parse_trace_file(trace_file):
    lines = open(trace_file).readlines()
    generation = []
    flows = []
    unfinished = []
    conf = []
    for line in lines:
        if (re.search("Generating", line) is not None):
            generation.append(line)
        elif (re.search("^Unfinished", line) is not None):
            unfinished.append(line)
        elif (re.search("^\d", line) is not None):
            flows.append(line)
        else:
            conf.append(line)
    return conf, generation, flows, unfinished

def parse_flow(flow):
    fid, size, src, dst, start, finish, fct, oraclefct, normfct = flow.split()
    return (int(size), float(fct), float(oraclefct), float(normfct))

def parse_unfinished(unfinished):
    _, fid, size, src, dst, start = unfinished.split()
    return (int(size), float(start))

def sanity_check_unfinished(conf, unfins):
    endtime = get_end_time(conf)
    for unfin in unfins:
        u = parse_unfinished(unfin)
        if (u[1] >= endtime):
            print 'flow started after end: ', u
            assert(False)

def get_end_time(conf):
    for line in conf:
        if (re.search("^Running Until", line) is not None):
            return float(line.split()[-1])*1e6
def get_avg_fct(conf):
    for line in conf:
        if (re.search("^AverageFCT", line) is not None):
            return float(line.split()[1])

def bucketize(flows):
    #could be either unfinished or not, so only check first tuple index
    #manual bucketization
    # 1 packet, 2 packet, 3 packet, 4381-10220, 10221-105120, 105121-500000, 500000-1000000, 1000000 - 2000000, 2000000-onward
    # the labels will be
    # 'All', '1Pkt', '2Pkt', '3Pkt', '5KB-10KB', '10KB-100KB', '100KB-500KB', '500KB-1MB', '1MB-2MB', '>2MB'

    bucketized = {};

    packetSize = 1460
    buckets = [0, packetSize, packetSize*2, packetSize*3, 10220, 105120, 500000, 1e6, 2e6]

    for b in buckets:
        bucketized[b] = []

    for f in flows:
        if (f[0] > buckets[-1]):
            bucketized[buckets[-1]].append(f)
            continue
        for i in range(len(buckets)-1):
          if (f[0] > buckets[i] and f[0] <= buckets[i+1]):
            bucketized[buckets[i]].append(f)
            break;
    return bucketized

def check_unfinished_flows_finishing_chance(conf, unfins):
    endtime = get_end_time(conf)
    avgfct = get_avg_fct(conf)
    real_endtime = endtime - avgfct
    before_count = 0
    after_count = 0
    for u in unfins:
        if (u[1] < real_endtime):
            before_count += 1
        else:
            after_count += 1
    print 'fraction of unfinished started within avgfct of end', after_count/len(unfins)

def unfinished_flows_fraction_by_size(flows, unfins):
    flows_by_size = bucketize(flows)
    unfins_by_size = bucketize(unfins)
    print 'Fraction of Flows left Unifinished By Size'
    for size in sorted(unfins_by_size.keys()):
        total_flows_in_size = len(unfins_by_size[size]) + len(flows_by_size[size])
        print size, len(unfins_by_size[size]), len(unfins_by_size[size])/total_flows_in_size

def unfinished_flows_by_size(unfins):
    unfins_by_size = bucketize(unfins)
    total_unfin = len(unfins)
    print 'Unfinished Flows by size'
    for size in sorted(unfins_by_size.keys()):
        print size, len(unfins_by_size[size]), len(unfins_by_size[size]) / total_unfin
conf, gen, flows, unfins = parse_trace_file(flow_trace)

sanity_check_unfinished(conf, unfins)

flows = [parse_flow(f) for f in flows]
unfins = [parse_unfinished(f) for f in unfins]

check_unfinished_flows_finishing_chance(conf, unfins)
unfinished_flows_fraction_by_size(flows, unfins)
unfinished_flows_by_size(unfins)
