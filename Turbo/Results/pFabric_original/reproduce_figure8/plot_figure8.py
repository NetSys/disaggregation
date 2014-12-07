import sys
sys.path.insert(0, '..')
import numpy
import plotter

import parse_trace as parse
import ideal as ideal

"""
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
"""

def main():
  loads = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]
  norm_fct_ideal_all = []
  norm_fct_ideal_sf_all = []
  norm_fct_pfabric_all = []
  norm_fct_ideal_large = []
  norm_fct_ideal_sf_large = []
  norm_fct_pfabric_large = []

  for l in loads:
    print "plotting on", l, "load"
    f = open("./Dataset/flow_"+str(l)+"Load_large.tr").readlines()
    #Flow info is array: [size fct oracle_fct norm_fct]
    flow_info = parse.get_flow_info_new(f, 2.5) #Dictionary with indices as keys
    f = open("./Dataset/ideal_"+str(l)+"Result_large.txt").readlines()
    ideal_fct = [float(x) for x in f]
    f = open("./Dataset/ideal_"+str(l)+"Result_large.txt").readlines()
    ideal_sf_fct = [float(x) for x in f]
    norm_fct_ideal = [x / y[2] for x, y in zip(ideal_fct, flow_info)]
    norm_fct_ideal_sf = [x / y[2] for x, y in zip(ideal_sf_fct, flow_info)]
    norm_fct_ideal_all.append(numpy.mean(norm_fct_ideal))
    norm_fct_ideal_sf_all.append(numpy.mean(norm_fct_ideal_sf))
    norm_fct_pfabric_all.append(numpy.mean([x[3] for x in flow_info]))
  
    large_indices = [i for i in range(len(flow_info)) if flow_info[i][0] >= 10000000]
    large_ideal_fct = [ideal_fct[i] for i in large_indices]
    large_ideal_sf_fct = [ideal_sf_fct[i] for i in large_indices]
    large_flow_info = [flow_info[i] for i in large_indices]
    norm_large_fct_ideal = [x / y[2] for x, y in zip(large_ideal_fct, large_flow_info)]
    norm_large_fct_ideal_sf = [x / y[2] for x, y in zip(large_ideal_sf_fct, large_flow_info)]
    norm_fct_ideal_large.append(numpy.mean(norm_large_fct_ideal))
    norm_fct_ideal_sf_large.append(numpy.mean(norm_large_fct_ideal_sf))
    norm_fct_pfabric_large.append(numpy.mean([x[3] for x in large_flow_info]))

  x = loads
  plotter.PlotN([x, x, x], [norm_fct_ideal_all, norm_fct_ideal_sf_all, norm_fct_pfabric_all], 
                YTitle='Normalized FCT', XTitle='Load', 
                labels=['Ideal High', 'Ideal Low', 'pFabric'], 
                xAxis=[0.099, max(x)], yAxis=[0, max(max(norm_fct_ideal_all), max(norm_fct_ideal_sf_all), max(norm_fct_pfabric_all))], 
                outputFile="Figure7AllFlowsLarge")
  plotter.PlotN([x, x, x], [norm_fct_ideal_large, norm_fct_ideal_sf_large, norm_fct_pfabric_large], 
                YTitle='Normalized FCT', XTitle='Load',
                labels=['Ideal High', 'Ideal Low', 'pFabric'], 
                xAxis=[0.099, max(x)], yAxis=[0, max(max(norm_fct_ideal_large), max(norm_fct_ideal_sf_large), max(norm_fct_pfabric_large))], 
                outputFile="Figure8LargeFlowsLarge")


if __name__ == '__main__':
    main()
