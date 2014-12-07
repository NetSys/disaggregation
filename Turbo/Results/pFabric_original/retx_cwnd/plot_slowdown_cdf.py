import sys
sys.path.insert(0, '../..')
import numpy
import plotter

import parse_ns2_trace as parse
import ideal as ideal


def plot_cdf(f1, f2, f3,
             output):
  Y = [1.0 * i / len(f1) for i in range(len(f1))]
  X1 = sorted(f1)
  X2 = sorted(f2)
  X3 = sorted(f3)
  print numpy.mean(X1), numpy.mean(X2), numpy.mean(X3)
  plotter.PlotN([X1, X2, X3], \
    [Y, Y, Y], \
    YTitle='CDF', XTitle='Slowdown in FCT', \
    labels=['pFabric', 'Ideal', 'No Cwnd Reset'], \
    legendLoc='lower right', legendOff=False,\
    figSize=[7.8, 2.6], onlyLine=True,\
    lWidth=2, mSize=8, legendSize=18,\
    xAxis=[0, max(max(X3), max(X2))], yAxis=[0, 1],
    outputFile=output)



def main():
  loads = ['0.8Load']
  for load in loads:
    print load
    f_pf = parse.get_flow_info_new(open('Dataset/pf_' + load + '.tr').readlines(), 2.5) 
    f_id = [float(x) for x in open('Dataset/ideal_' + load + '.txt').readlines()]
    f_pf_no_cwnd_reset = parse.get_flow_info_new(open('Dataset/pf_no_cwnd_reset_' + load + '.tr').readlines(), 2.5) 
    
    norm_pf = [x[3] for x in f_pf]
    norm_id = [f_id[i] / f_pf[i][2] for i in range(len(f_id))]
    norm_pf_no_cwnd_reset = [x[3] for x in f_pf_no_cwnd_reset]
    plot_cdf(norm_pf, norm_id, norm_pf_no_cwnd_reset, 'SlowdownCdf_' + load)

main()