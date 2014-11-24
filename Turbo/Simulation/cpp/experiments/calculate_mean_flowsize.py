#!/usr/bin/python

import sys
import os

if (len(sys.argv) != 2):
  print "Wrong number of args: {}".format(len(sys.argv))
  print "Usage: ./find_mean_flowsize <CDF_File>"
  exit()

CDF_File = sys.argv[-1]

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
print mean_flow_size
