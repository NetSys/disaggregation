#!/usr/bin/python

import fileinput

def read_flowtrace(filename):
    f = open(filename)
    f = f.readlines()
    return f

def get_longflows(flows, thresh=1000000):
    longflows = []
    nonlongflows = []
    for x in flows:
        if (int(x.split()[1]) > thresh):
            longflows.append(x)
        else:
            nonlongflows.append(x)
    return longflows, nonlongflows

def get_average_slowdown(flows):
    return sum([float(x.split()[8]) for x in flows])/len(flows)

def get_average_fct(flows):
    return sum([float(x.split()[6]) for x in flows])/len(flows)

def get_start_range(flows):
    start = lambda x:float(x.split()[4])
    return min(flows, key=start), max(flows, key=start)

def get_end_range(flows):
    end = lambda x:float(x.split()[5])
    return min(flows, key=end), max(flows, key=end)

def get_finishing_cdf(flows):
    end = lambda x:float(x.split()[5])
    flows_sorted = sorted(flows, key=end)
    total_num = len(flows)
    additional_fraction = 1.0/total_num
    cdf_points = []
    cumulative_fraction = additional_fraction
    for flow in flows_sorted:
        cdf_points.append((end(flow), cumulative_fraction))
        cumulative_fraction += additional_fraction
    return cdf_points

flows = [x for x in fileinput.input()]
print 'slowdown: ', get_average_slowdown(flows)
print 'avrg fct: ', get_average_fct(flows)



