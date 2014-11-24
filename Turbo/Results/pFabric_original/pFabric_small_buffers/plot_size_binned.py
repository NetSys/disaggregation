import sys
sys.path.insert(0, '../..')
import numpy
import plotter

import parse_ns2_trace as parse
import ideal as ideal



def plot_norm_binned(f_pf, f_id, f_pf_lowbdp, f_pf_lowbdp_dumb_core, output):
  max_size = max([x[0] for x in f_pf])
  # split in 10KB chunks
  bin_size = 100000
  num_bins = 1 + int(max_size / bin_size)
  pf_binned = [[] for i in range(num_bins)]
  ideal_binned = [[] for i in range(num_bins)]
  lowbdp_binned = [[] for i in range(num_bins)]
  lowbdp_dumbcore_binned = [[] for i in range(num_bins)]
  for i in range(len(f_pf)):
    pf = f_pf[i]; id = f_id[i]; 
    low_bdp = f_pf_lowbdp[i]; lowbdp_dumbcore = f_pf_lowbdp_dumb_core[i]
    pf_binned[int(pf[0] / bin_size)].append(pf[3])
    ideal_binned[int(pf[0] / bin_size)].append(id / pf[2])
    lowbdp_binned[int(low_bdp[0] / bin_size)].append(low_bdp[3])
    lowbdp_dumbcore_binned[int(lowbdp_dumbcore[0] / bin_size)].append(lowbdp_dumbcore[3])

  avg_pf_binned = [numpy.mean(x) for x in pf_binned]
  avg_id_binned = [numpy.mean(x) for x in ideal_binned]
  avg_lowbdp_binned = [numpy.mean(x) for x in lowbdp_binned]
  avg_lowbdp_dumbcore_binned = [numpy.mean(x) for x in lowbdp_dumbcore_binned]
  x = range(num_bins)
  plotter.PlotN([x, x, x, x], 
    [avg_pf_binned, avg_id_binned, avg_lowbdp_binned, avg_lowbdp_dumbcore_binned], \
    YTitle='Mean Slowdown', XTitle='Bin (10KB)', \
    labels=['pFabric', 'Ideal', 'LowBDP', 'LowBDP/DumbCore'], 
    legendLoc='upper left', legendOff=False,\
    figSize=[7.8, 2.6], onlyLine=True,\
    lWidth=2, mSize=8, legendSize=18,\
    xAxis=[0, num_bins], yAxis=[0, max(avg_lowbdp_dumbcore_binned)],
    outputFile=output)


def main():
  loads = ['0.8Load']
  for load in loads:
    print load
    f_pf = parse.get_flow_info_new(open('Dataset/pf_' + load + '.tr').readlines(), 0) 
    f_id = [float(x) for x in open('Dataset/ideal_pF_' + load + '.tr').readlines()]
    f_pf_lowbdp = parse.get_flow_info_new(open('Dataset/low_bdp_' + load + '.tr').readlines(), 0) 
    f_pf_lowbdp_dumb_core = parse.get_flow_info_new(open('Dataset/low_bdp_dumbcore_' + load + '.tr').readlines(), 0) 
    
    plot_norm_binned(f_pf, f_id, f_pf_lowbdp, f_pf_lowbdp_dumb_core, 'MeanSlowdownBinned_' + load)

main()