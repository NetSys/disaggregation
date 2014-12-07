import sys
sys.path.insert(0, '..')
import numpy
import plotter

import parse_trace as parse
import ideal as ideal

def main():
  loads = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]
  norm_fct_ideal_all = []
  norm_fct_pfabric_all = []

  norm_avg_fct_ideal_all = []
  norm_avg_fct_pfabric_all = []

  norm_fct_ideal_large = []
  norm_fct_pfabric_large = []

  norm_avg_fct_ideal_large = []
  norm_avg_fct_pfabric_large = []

  for l in loads:
    print "plotting on", l, "load"
    f = open("./Dataset/aditya_pfabric_"+str(l)+".tr").readlines()
    #Flow info is array: [size fct oracle_fct norm_fct]
    flow_info = parse.get_flow_info_new(f, 2.5) #Dictionary with indices as keys
    f = open("./Dataset/aditya_ideal_"+str(l)+".txt").readlines()
    ideal_fct = [float(x) for x in f]
    norm_fct_ideal = [x / y[2] for x, y in zip(ideal_fct, flow_info)]
    norm_fct_ideal_all.append(numpy.mean(norm_fct_ideal))
    norm_fct_pfabric_all.append(numpy.mean([x[3] for x in flow_info]))
  
    norm_avg_fct_ideal_all.append(numpy.mean([x for x in ideal_fct]) / 
                                  numpy.mean([x[2] for x in flow_info]))
    norm_avg_fct_pfabric_all.append(numpy.mean([x[1] for x in flow_info]) / 
                                  numpy.mean([x[2] for x in flow_info]))
 
    large_indices = [i for i in range(len(flow_info)) if flow_info[i][0] >= 100000] #1MB
    large_ideal_fct = [ideal_fct[i] for i in large_indices]
    large_flow_info = [flow_info[i] for i in large_indices]
    norm_large_fct_ideal = [x / y[2] for x, y in zip(large_ideal_fct, large_flow_info)]
    norm_fct_ideal_large.append(numpy.mean(norm_large_fct_ideal))
    norm_fct_pfabric_large.append(numpy.mean([x[3] for x in large_flow_info]))

    norm_avg_fct_ideal_large.append(numpy.mean([x for x in large_ideal_fct]) / 
                                  numpy.mean([x[2] for x in large_flow_info]))
    norm_avg_fct_pfabric_large.append(numpy.mean([x[1] for x in large_flow_info]) / 
                                  numpy.mean([x[2] for x in large_flow_info]))


  x = loads
  plotter.PlotN([x, x], [norm_fct_ideal_all, norm_fct_pfabric_all], 
                YTitle='Normalized FCT', XTitle='Load', 
                labels=['Ideal', 'pFabric'], 
                xAxis=[0.099, max(x)], yAxis=[0, max(max(norm_fct_ideal_all), max(norm_fct_pfabric_all))], 
                outputFile="AllFlowsSlowdown")
  plotter.PlotN([x, x], [norm_fct_ideal_large, norm_fct_pfabric_large], 
                YTitle='Normalized FCT', XTitle='Load',
                labels=['Ideal', 'pFabric'], 
                xAxis=[0.099, max(x)], yAxis=[0, max(max(norm_fct_ideal_large), max(norm_fct_pfabric_large))], 
                outputFile="LargeFlowsSlowdown")
  plotter.PlotN([x, x], [norm_avg_fct_ideal_all, norm_avg_fct_pfabric_all], 
                YTitle='Normalized Avg FCT', XTitle='Load', 
                labels=['Ideal', 'pFabric'], 
                xAxis=[0.099, max(x)], yAxis=[0, max(max(norm_avg_fct_ideal_all), max(norm_avg_fct_pfabric_all))], 
                outputFile="AllFlowsAvg")
  plotter.PlotN([x, x], [norm_avg_fct_ideal_large, norm_avg_fct_pfabric_large], 
                YTitle='Normalized Avg FCT', XTitle='Load',
                labels=['Ideal', 'pFabric'],
                xAxis=[0.099, max(x)], yAxis=[0, max(max(norm_avg_fct_ideal_large), max(norm_avg_fct_pfabric_large))], 
                outputFile="LargeFlowsAvg")


if __name__ == '__main__':
    main()
