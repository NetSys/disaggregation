import sys
sys.path.insert(0, '../..')
import numpy
import plotter

import parse_ns2_trace as parse
import ideal as ideal



def plot_norm_binned(f_pf, f_id, f_pf_no_cwnd_reset, output):
  max_size = max([x[0] for x in f_pf])
  # split in 10KB chunks
  bin_size = 100000
  num_bins = 1 + int(max_size / bin_size)
  pf_binned = [[] for i in range(num_bins)]
  ideal_binned = [[] for i in range(num_bins)]
  pf_no_cwnd_reset_binned = [[] for i in range(num_bins)]
  for i in range(len(f_pf)):
    pf = f_pf[i]; id = f_id[i]; 
    pf_no_cwnd_reset = f_pf_no_cwnd_reset[i];
    pf_binned[int(pf[0] / bin_size)].append(pf[3])
    ideal_binned[int(pf[0] / bin_size)].append(id / pf[2])
    pf_no_cwnd_reset_binned[int(pf_no_cwnd_reset[0] / bin_size)].append(pf_no_cwnd_reset[3])

  avg_pf_binned = [numpy.mean(x) for x in pf_binned]
  avg_id_binned = [numpy.mean(x) for x in ideal_binned]
  avg_pf_no_cwnd_reset_binned = [numpy.mean(x) for x in pf_no_cwnd_reset_binned]
  x = range(num_bins)
  plotter.PlotN([x, x, x], 
    [avg_pf_binned, avg_id_binned, avg_pf_no_cwnd_reset_binned], \
    YTitle='Mean Slowdown', XTitle='Bin (10KB)', \
    labels=['pFabric', 'Ideal', 'No Cwnd Reset'], 
    legendLoc='upper left', legendOff=False,\
    figSize=[7.8, 2.6], onlyLine=True,\
    lWidth=2, mSize=8, legendSize=18,\
    xAxis=[0, num_bins], yAxis=[0, max(avg_pf_no_cwnd_reset_binned)],
    outputFile=output)


def main():
  loads = ['0.8Load']
  for load in loads:
    print load
    f_pf = parse.get_flow_info_new(open('Dataset/pf_' + load + '.tr').readlines(), 0) 
    f_id = [float(x) for x in open('Dataset/ideal_' + load + '.txt').readlines()]
    f_pf_no_cwnd_reset = parse.get_flow_info_new(open('Dataset/pf_no_cwnd_reset_' + load + '.tr').readlines(), 0) 
    
    plot_norm_binned(f_pf, f_id, f_pf_no_cwnd_reset, 'MeanSlowdownBinned_' + load)

main()