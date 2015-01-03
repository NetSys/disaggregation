import sys
sys.path.insert(0, '../..')
import numpy
import plotter

import parse_ns2_trace as parse
import ideal as ideal


def plot_cdf(fct, fct_large, 
             output):
  Y1 = [1.0 * i / len(fct) for i in range(len(fct))]
  Y2 = [1.0 * i / len(fct_large) for i in range(len(fct_large))]
  X1 = sorted(fct)
  X2 = sorted(fct_large)
  #X3 = sorted(ideal_fct)
  #X4 = sorted(ideal_fct_large)
  plotter.PlotN([X1, X2], \
    [Y1, Y2], \
    YTitle='CDF', XTitle='Mean Slowdown', \
    labels=['All', '>10MB'], \
    legendLoc='lower right', legendOff=False,\
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
  loads = ['0.8Load', '0.8Load_large', '0.8Load_xlarge', '0.8Load_xxlarge']
  for load in loads:
    print load
    f = open('Dataset/flow_' + load + '.tr').readlines()[:-1]
    f2 = open('Dataset/ideal_' + load + '.txt').readlines()[:-1]
    flow_info = parse.get_flow_info_new(f, 2.5) #Dictionary with indices as keys

    large_flow_indices = [i for i in range(len(flow_info)) if flow_info[i][0] >= 10000000]
    norm_ideal = [float(f2[i]) / flow_info[i][2] for i in range(len(f2))]

    norm_pFabric = [x[3] for x in flow_info]
    norm_pFabric_large = [norm_pFabric[i] for i in large_flow_indices]

    norm_ideal = [float(f2[i]) / flow_info[i][2] for i in range(len(f2))]
    norm_ideal_large = [norm_ideal[i] for i in large_flow_indices]
    print max(norm_pFabric), max(norm_ideal)
    plot_cdf(norm_pFabric, norm_pFabric_large, 
      'NormalizedFctCdf_pFabric' + load)
    plot_cdf(norm_ideal, norm_ideal_large, 
      'NormalizedFctCdf_ideal' + load)


main()
  #return large_flow_info

