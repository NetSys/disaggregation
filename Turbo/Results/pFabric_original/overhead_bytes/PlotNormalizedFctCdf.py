import sys 
import numpy
import plotter
def get_statistics(f, switch_delay):
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
  
  
    pd = 2 * hops[i] * switch_delay #in us (host delay + switch delay)
    td = (flow_size[i] + 1460)* 8.0 / (10000.0) #us (fs + first)
    if hops[i] == 4:
      td += 2 * 1460.0 * 8.0 / (40000.0) #transmission delay of above nodes
    oracle_fct.append(pd + td) 


  #for x in outliers:
  #  print x
  norm_fct = [x / y for x, y in zip(fct, oracle_fct)]
  print sum(fct) / sum(oracle_fct)
  norm_fct_big = [norm_fct[i] for i in range(len(norm_fct)) if flow_size[i] >= 10000000]
  return flow_size, norm_fct

lines = open(sys.argv[1]).readlines()
switch_delay = float(sys.argv[2])
lines = [x for x in lines if len(x.split()) > 3]
flow_size, norm_fct = get_statistics(lines, switch_delay)

X = [1.0 * i / len(flow_size) for i in range(len(flow_size))]
Y = sorted(norm_fct)

plotter.PlotN([Y], [X], \
  YTitle='CDF', XTitle='Normalized FCT', \
  labels=['PFabric (Exact Experiment)', 'PFabric (No Host Delay)'], legendLoc='upper right', legendOff=True,\
  figSize=[7.8, 2.6], onlyLine=True,\
  lWidth=2, mSize=8, legendSize=18,\
  xAxis=[0, 100], yAxis=[0, 1],
  outputFile="NormalizedFctCdf")

fct = {}
for i in range(len(norm_fct)):
  fct[norm_fct[i]] = flow_size[i]

#for x in sorted(fct.keys()):
#  print fct[x], x
per_byte_fct = [norm_fct[i] * flow_size[i] for i in range(len(norm_fct))]
total_bytes = sum(flow_size)

print sum(per_byte_fct) / total_bytes * 1.0, numpy.mean(norm_fct)


