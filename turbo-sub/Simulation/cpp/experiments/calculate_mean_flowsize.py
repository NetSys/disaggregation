#!/usr/bin/python

import sys

def get_mean_flowsize(cdf):
    CDF_File = cdf

    f = open(CDF_File).readlines()
    f = [z for z in f if len(z.split()) == 3]
    f = [[float(x.split()[0]), float(x.split()[-1])] for x in f]

    total_percentage = f[0][1]
    mean_packets = f[0][0] * total_percentage
    for i in range(len(f) - 1):
      marginal_percentage = f[i+1][1] - f[i][1]
      mean_packets += marginal_percentage * 0.5 * (f[i+1][0] + f[i][0])
      total_percentage += marginal_percentage
    assert(total_percentage == 1.0)

    mean_flow_size = 1460 * mean_packets
    return mean_flow_size

if __name__ == '__main__':
    if (len(sys.argv) != 2):
      print "Wrong number of args: {}".format(len(sys.argv))
      print "Usage: ./find_mean_flowsize <CDF_File>"
      exit()

    print get_mean_flowsize(sys.argv[-1])
