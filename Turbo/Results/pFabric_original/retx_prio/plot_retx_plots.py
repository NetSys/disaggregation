import sys
sys.path.insert(0, '..')
import numpy
import plotter

import parse_trace as parse
import ideal as ideal

def plot_cdf_large_flows(flow_info, large_flow_info, output):
  Y1 = [1.0 * i / len(flow_info) for i in range(len(flow_info))]
  X1 = sorted([x[3] for x in flow_info])
  Y2 = [1.0 * i / len(large_flow_info) for i in range(len(large_flow_info))]
  X2 = sorted([x[3] for x in large_flow_info])
  plotter.PlotN([X1, X2], [Y1, Y2], \
    YTitle='CDF', XTitle='Normalized FCT', \
    labels=['All', '>10MB'], legendLoc='lower right', legendOff=False,\
    figSize=[7.8, 2.6], onlyLine=True,\
    lWidth=2, mSize=8, legendSize=18,\
    xAxis=[0, max(max(X1), max(X2))], yAxis=[0, 1],
    outputFile=output)

def plot_norm_binned(flow_info, ideal_fct, output):
  max_size = max([x[0] for x in flow_info])
  # split in 100KB chunks
  bin_size = 100000
  num_bins = 1 + int(max_size / bin_size)
  norm_fct_binned = [[] for i in range(num_bins)]
  norm_fct_ideal_binned = [[] for i in range(num_bins)]
  for i in range(len(flow_info)):
    f = flow_info[i]
    bin = int(f[0] / bin_size)
    norm_fct_binned[bin].append(f[3])
    norm_fct_ideal_binned[bin].append(ideal_fct[i] / f[2])
  avg_norm_fct_binned = [numpy.mean(x) for x in norm_fct_binned]
  avg_norm_fct_ideal_binned = [numpy.mean(x) for x in norm_fct_ideal_binned]
  x = range(num_bins)
  plotter.PlotN([x, x], [avg_norm_fct_binned, avg_norm_fct_ideal_binned], \
    YTitle='Avg. Norm FCT', XTitle='Bin (100KB)', \
    labels=['pFabric', 'Ideal'], legendLoc='upper left', legendOff=False,\
    figSize=[7.8, 2.6], onlyLine=True,\
    lWidth=2, mSize=8, legendSize=18,\
    xAxis=[0, num_bins], yAxis=[0, max(avg_norm_fct_binned)],
    outputFile=output)

def plot_norm_timed(flow_info, ideal_fct, output):
  # split in 100 chunks
  num_bins = 100
  bin_size = len(flow_info) / num_bins
  norm_fct_binned = [[] for i in range(num_bins)]
  for i in range(len(flow_info)):
    f = flow_info[i]
    bin = int(i / bin_size)
    norm_fct_binned[bin].append(f[3])
  avg_norm_fct_binned = [numpy.mean(x) for x in norm_fct_binned]
  x = range(num_bins)
  plotter.PlotN([x], [avg_norm_fct_binned], \
    YTitle='Avg. Norm FCT', XTitle='Bin (' + str(bin_size) + ' flows)', \
    labels=['All', '>10MB'], legendLoc='lower right', legendOff=True,\
    figSize=[7.8, 2.6], onlyLine=True,\
    lWidth=2, mSize=8, legendSize=18,\
    xAxis=[0, num_bins], yAxis=[0, max(avg_norm_fct_binned)],
    outputFile=output)


def plot_size_timed(flow_info, ideal_fct, output):
  # split in 100 chunks
  num_bins = 100
  bin_size = len(flow_info) / num_bins
  size_timed = [[] for i in range(num_bins)]
  for i in range(len(flow_info)):
    f = flow_info[i]
    bin = int(i / bin_size)
    size_timed[bin].append(f[0] / 1000000.0)
  avg_size_timed = [numpy.mean(x) for x in size_timed]
  #print avg_size_timed
  max_size_timed = [max(x) for x in size_timed]
  #print avg_size_timed
  x = range(num_bins)
  plotter.PlotN([x, x], [avg_size_timed, max_size_timed], \
    YTitle='Size (MB)', XTitle='Bin (' + str(bin_size) + ' flows)', \
    labels=['Avg.', 'Max'], legendLoc='center right', legendOff=False,\
    figSize=[7.8, 2.6], onlyLine=True,\
    lWidth=2, mSize=8, legendSize=18,\
    xAxis=[0, num_bins], yAxis=[0, 35],
    outputFile=output)


def main():
  load = '0.9Load_large.tr'
  f = open('Dataset/flow_' + load).readlines()
  f2 = open('Dataset/ideal_' + load).readlines()
  flow_info = parse.get_flow_info_new(f, 2.5) #Dictionary with indices as keys
  ideal_fct = [float(x) for x in f2]
  large_flow_indices = [i for i in range(len(flow_info)) if flow_info[i][0] >= 10000000]
  large_flow_info = [flow_info[i] for i in large_flow_indices]
  ideal_large_flow = [ideal_fct[i] for i in large_flow_indices]
  plot_cdf_large_flows(flow_info, large_flow_info, 'NormalizedFctCdf_' + load)
  plot_norm_binned(flow_info, ideal_fct, 'NormalizedFctBinned_' + load)
  plot_norm_timed(flow_info, ideal_fct, 'NormalizedFctTimed_' + load)
  plot_size_timed(flow_info, ideal_fct, 'SizeTimed_' + load)


main()
  #return large_flow_info
"""
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


"""