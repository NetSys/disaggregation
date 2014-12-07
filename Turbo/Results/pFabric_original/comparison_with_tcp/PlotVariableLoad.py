#!/usr/bin/env python
import sys
import os
import math
import plotter
import numpy

#NoHostDelay
def print_statistics(f, host_delay):
  flow_size = [1460 * float(x.split()[0]) for x in f]
  hops = []
  for x in f:
    s = float(x.split()[3])
    d = float(x.split()[4])
    if (s/16) == (d/16):
      hops.append(2)
    else:
      hops.append(4)

  fct = [1000000 * float(x.split()[1]) for x in f] #fct in us
  oracle_fct = []
  outliers = []
  for i in range(len(f)):
  
  
    pd = 4 * host_delay + 2 * hops[i] * 0.2 #in us (host delay + switch delay)
    td = (flow_size[i] + 1460)* 8.0 / (10000.0) #us (fs + first)
    if hops[i] == 4:
      td += 2 * 1460.0 * 8.0 / (40000.0)
    oracle_fct.append(pd + td)


  #for x in outliers:
  #  print x
  norm_fct = [x / y for x, y in zip(fct, oracle_fct)]
  norm_fct_big = [norm_fct[i] for i in range(len(norm_fct)) if flow_size[i] >= 10000000]

  #print numpy.mean(oracle_fct), numpy.mean(fct), numpy.mean(fct) / numpy.mean(oracle_fct),
  #print numpy.mean(norm_fct), numpy.mean(norm_fct_big)
  return numpy.mean(norm_fct)

load = [0.1 * (x + 1) for x in range(9)]
Y1 = [2.71, 2.52, 2.35, 2.17, 1.97, 1.79, 1.61, 1.44, 1.31]
Y2 = [10.26, 9.56, 8.87, 8.21, 7.61, 7.06, 6.58, 6.17, 5.96]#3, 4.5, 9, 18, 36]
Y3 = [31.36, 28.04, 24.87, 21.90, 19.11, 16.73, 14.62, 12.82, 11.43]

plotter.PlotN([load, load, load], [Y1, Y2, Y3], \
	XTitle='%of short flows', YTitle='Normalized FCT', \
	labels=['PFabric (Exact Experiment)', 'PFabric (No Host Delay) + 3pkt', 'PFabric (No Host Delay) + 2pkt'], legendLoc='upper right',\
	figSize=[7.8, 2.6],
	lWidth=2, mSize=8, legendSize=15,\
	yAxis=[0, 35], xAxis=[0, 1],
	outputFile="Compare")


