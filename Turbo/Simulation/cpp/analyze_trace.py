#!/usr/bin/python

import sys
import itertools
import numpy as np
import plotter

print sys.argv

# if (len(sys.argv) != 2):
#   print "Usage: ./analyze_trace.py <trace file>"
#   exit()

def readTrace(filename, trace):
  print trace[-1]
  print trace[-2]
  flowsBySize = {}

  overall = {}
  #overall['deadPackets'] = formatify(float,trace,-1,-1)*100
  for line in trace:
    if "AverageFCT" in line:
      print "Here"
      overall['averageFCT'] = float(line.split()[1])
      overall['meanSlowdown'] = float(line.split()[3])
      continue
    if (len(line.split()) != 9):
      continue
    #5 1460 4 10 2.09599999956 2.096 0.999999999791
    l = line.split()
    fct = float(l[6])
    slowdown = float(l[8])
    size = float(l[1])
    flow = {'slowdown':slowdown, 'fct':fct, 'size':size, 'line':line}
    if (size in flowsBySize.keys()):
      flowsBySize[size].append(flow)
    else:
      flowsBySize[size] = [flow]

  flowsBySize = bucketize(flowsBySize)

  formatify = lambda res,tr,i,j:res(tr[i].split()[j])


  data = {}
  data['flowsBySize'] = flowsBySize
  data['overall'] = overall
  data['experiment'] = filename


  return data

def bucketize(flowsBySize, numberOfBuckets=10):
  if (numberOfBuckets <= 0):
    assert(False,'numberOfBuckets must be positive')
  if (len(flowsBySize.keys()) <= numberOfBuckets):
    return flowsBySize
  #else, need to bucketize!

  #manual bucketization
#   1 packet, 2 packet, 3 packet, 4381-10220, 10221-105120, 105121-500000, 500000-1000000, 1000000 - 2000000, 2000000-onward
# the labels will be
# 'All', '1Pkt', '2Pkt', '3Pkt', '5KB-10KB', '10KB-100KB', '100KB-500KB', '500KB-1MB', '1MB-2MB', '>2MB'

  bucketized = {};

  packetSize = 1460
  buckets = [0, packetSize, packetSize*2, packetSize*3, 10220,
             105120, 500000, 1e6, 2e6]

  for b in buckets:
    bucketized[b] = []

  for size in flowsBySize:
    if (size > buckets[-1]):
      bucketized[buckets[-1]] += flowsBySize[size]
      continue
    for i in range(len(buckets)-1):
      if (size > buckets[i] and size <= buckets[i+1]):
        bucketized[buckets[i]] += flowsBySize[size]
        break;

  for b in buckets:
    print b
    print min(bucketized[b]), max(bucketized[b]), np.mean([x['slowdown'] for x in bucketized[b]])
  return bucketized

def callPlot(xaxis,yaxis,xtitle,ytitle,labels,filename,ylim=None):
  #xaxis = range(len(yaxis[0]))
  xlimits = (0,len(xaxis) + 1)
  ylimits = ylim if ylim else (min([min(t) for t in yaxis]), max([max(t) for t in yaxis]))
  plotter.PlotBarChart(xaxis, yaxis, xAxis=xlimits, yAxis=ylimits,
    XTitle=xtitle, YTitle=ytitle, labels=labels, outputFile=filename, legendSize=30,
    figSize = [25.0, 7.0])

def plotSlowdowns(datas):
  yaxis = []

  for data in datas:
    bySize = {size:np.mean([flow['slowdown'] for flow in data['flowsBySize'][size]]) for size in sorted(data['flowsBySize'].keys())}
    yaxis.append([data['overall']['meanSlowdown']] + [bySize[size] for size in sorted(bySize)])

  xaxis = ['All', '1Pkt', '2Pkt', '3Pkt', '5KB-10KB', '10KB-100KB', '100KB-500KB', '500KB-1MB', '1MB-2MB', '>2MB']
  labels = [data['experiment'] for data in datas]
  callPlot(xaxis,yaxis,'Sizes','Slowdown', labels, 'slowdowns', ylim = (0,1.1*max([max(t) for t in yaxis])))

def plotAverageFCTs(datas):
  yaxis = []
  for data in datas:
    bySize = {size:np.mean([x['fct'] for x in data['flowsBySize'][size]]) for size in sorted(data['flowsBySize'].keys())}
    yaxis.append([data['overall']['averageFCT']] + [bySize[size] for size in sorted(bySize)])

  xaxis = ['All', '1Pkt', '2Pkt', '3Pkt', '5KB-10KB', '10KB-100KB', '100KB-500KB', '500KB-1MB', '1MB-2MB', '>2MB']
  labels = [x['experiment'] for x in datas]
  callPlot(xaxis, yaxis,'Sizes','Avg FCT', labels, 'fcts', ylim = (0,1.1*max([max(t) for t in yaxis])))

"""
def plotDeadPackets(datas):
  yaxis = [[data['overall']['deadPackets'] for data in datas]]
  xaxis = [data['experiment'] for data in datas]
  callPlot(xaxis, yaxis, 'Experiment', 'DeadPackets', ['deadPackets'], 'deadpackets', ylim = (0,1.1*max(yaxis[0])))
"""

datas = [readTrace(filename, open(filename).readlines()) for filename in sys.argv[1:]]
plotSlowdowns(datas)
plotAverageFCTs(datas)
#plotDeadPackets(datas)
