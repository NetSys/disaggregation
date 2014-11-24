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


X1 = [3, 4.5, 7.5, 15, 30, 45]
Y1 = []
for x in [2, 3, 5, 10, 20, 30]:
  f = open("VaryingQueueSize_0.8Load_NoHostDelay/flowQ" + str(x) + ".tr").readlines()
  f = [x for x in f if len(x.split()) > 3]
  Y1.append(print_statistics(f, 0))
print Y1
#Y1 = [17.97, 6.96, 4.133, 2.28, 1.73, 1.73]

#Exact PFabric
X2 = [3, 4.5, 9, 18, 36]
Y2 = []
for x in [0.17, 0.25, 0.5, 1, 2]:
  f = open("VaryingQueueSize_0.8Load/flow" + str(x) + ".tr").readlines()
  f = [x for x in f if len(x.split()) > 3]
  Y2.append(print_statistics(f, 2.5))
print Y2

plotter.PlotN([X2, X1], [Y2, Y1], \
	XTitle='Buffer Size (KB)', YTitle='Normalized FCT', \
	labels=['PFabric (Exact Experiment)', 'PFabric (No Host Delay)'], legendLoc='upper right',\
	figSize=[7.8, 2.6],
	lWidth=2, mSize=8, legendSize=18,\
	yAxis=[0, 25], xAxis=[0, 45],
	outputFile="NoHostDelay")


