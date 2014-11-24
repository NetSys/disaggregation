import sys
sys.path.insert(0, '../../')
import numpy
import plotter

import parse_ns2_trace as parse
import ideal as ideal

def main():
  loads = [0.5, 0.6, 0.7, 0.8]

  #Slow Down metric 
  norm_fct_ideal_all = []
  norm_fct_pfabric_all = []
  norm_fct_low_bdp_all = []
  norm_fct_low_bdp_dumb_core_all = []


  norm_fct_ideal_large = []
  norm_fct_pfabric_large = []
  norm_fct_low_bdp_large = []	
  norm_fct_low_bdp_dumb_core_large = []	

  #Avg FCT metric
  avg_fct_ideal_all = []
  avg_fct_pfabric_all = []
  avg_fct_low_bdp_all = []
  avg_fct_low_bdp_dumb_core_all = []

  avg_fct_ideal_large = []
  avg_fct_pfabric_large = []
  avg_fct_low_bdp_large = []
  avg_fct_low_bdp_dumb_core_large = []

  for l in loads:
    print "Load: ", l
    #Flow info is array: [size fct oracle_fct norm_fct]
    finfo_pf = parse.get_flow_info_new(open("./Dataset/pF_"+str(l)+"Load.tr").readlines(), 0) 
    finfo_low_bdp = parse.get_flow_info_new(open("./Dataset/low_bdp_"+str(l)+"Load.tr").readlines(), 0) 
    finfo_low_bdp_dumb_core = parse.get_flow_info_new(open("./Dataset/low_bdp_dumbcore_"+str(l)+"Load.tr").readlines(), 0) 
    ideal_fct = [float(x) for x in open("./Dataset/ideal_pf_"+str(l)+"Load.tr").readlines()]

    norm_fct_ideal_all.append(numpy.mean([x / y[2] for x, y in zip(ideal_fct, finfo_pf)]))
    avg_fct_ideal_all.append(sum(ideal_fct) / sum([y[2] for y in finfo_pf]))

    norm_fct_pfabric_all.append(numpy.mean([x[3] for x in finfo_pf]))
    avg_fct_pfabric_all.append(sum([y[1] for y in finfo_pf]) / sum([y[2] for y in finfo_pf]))

    norm_fct_low_bdp_all.append(numpy.mean([x[3] for x in finfo_low_bdp]))
    avg_fct_low_bdp_all.append(sum([y[1] for y in finfo_low_bdp]) / sum([y[2] for y in finfo_low_bdp]))

    norm_fct_low_bdp_dumb_core_all.append(numpy.mean([x[3] for x in finfo_low_bdp_dumb_core]))
    avg_fct_low_bdp_dumb_core_all.append(sum([y[1] for y in finfo_low_bdp_dumb_core]) / 
    	sum([y[2] for y in finfo_low_bdp_dumb_core]))

    #Large flows for pf and ideal
    large_indices = [i for i in range(len(finfo_pf)) if finfo_pf[i][0] >= 10000000]
    large_ideal_fct = [ideal_fct[i] for i in large_indices]
    large_flow_info = [finfo_pf[i] for i in large_indices]
    norm_fct_ideal_large.append(numpy.mean([x / y[2] for x, y in zip(large_ideal_fct, large_flow_info)]))
    avg_fct_ideal_large.append(sum(large_ideal_fct) / sum([y[2] for y in large_flow_info]))


    large_flow_info = [finfo_pf[i] for i in large_indices]
    norm_fct_pfabric_large.append(numpy.mean([x[3] for x in large_flow_info]))
    avg_fct_pfabric_large.append(sum([y[1] for y in large_flow_info]) / sum([y[2] for y in large_flow_info]))

    #For Low BDP
    large_indices = [i for i in range(len(finfo_low_bdp)) if finfo_low_bdp[i][0] >= 10000000]
    large_flow_info = [finfo_low_bdp[i] for i in large_indices]
    norm_fct_low_bdp_large.append(numpy.mean([x[3] for x in large_flow_info]))
    avg_fct_low_bdp_large.append(sum([y[1] for y in large_flow_info]) / sum([y[2] for y in large_flow_info]))

    large_indices = [i for i in range(len(finfo_low_bdp_dumb_core)) if finfo_low_bdp_dumb_core[i][0] >= 10000000]
    large_flow_info = [finfo_low_bdp_dumb_core[i] for i in large_indices]
    norm_fct_low_bdp_dumb_core_large.append(numpy.mean([x[3] for x in large_flow_info]))
    avg_fct_low_bdp_dumb_core_large.append(sum([y[1] for y in large_flow_info]) / sum([y[2] for y in large_flow_info]))


 
  x = loads
  plotter.PlotN([x, x, x, x], 
  		[norm_fct_ideal_all, norm_fct_pfabric_all, norm_fct_low_bdp_all, norm_fct_low_bdp_dumb_core_all], 
        YTitle='Normalized FCT', XTitle='Load', 
       	labels=['Ideal', 'pFabric (Orig)', 'pFabric (LowBDP)', 'pFabric (LowBDP/DumbCore)'], 
        xAxis=[0.099, max(x)], 
        yAxis=[0, max(norm_fct_low_bdp_dumb_core_all)], 
        outputFile="Figure7AllFlows")
  plotter.PlotN([x, x, x, x], 
  		[norm_fct_ideal_large, norm_fct_pfabric_large, norm_fct_low_bdp_large, norm_fct_low_bdp_dumb_core_large], 
        YTitle='Normalized FCT', XTitle='Load',
        labels=['Ideal', 'pFabric (Orig)', 'pFabric (LowBDP)', 'pFabric (LowBDP/DumbCore)'], 
        xAxis=[0.099, max(x)], 
        yAxis=[0, max(norm_fct_low_bdp_dumb_core_large)], 
        outputFile="Figure8LargeFlows")

  plotter.PlotN([x, x, x, x], 
  		[avg_fct_ideal_all, avg_fct_pfabric_all, avg_fct_low_bdp_all, avg_fct_low_bdp_dumb_core_all], 
        YTitle='Ratio of Avg FCT', XTitle='Load', 
        labels=['Ideal', 'pFabric (Orig)', 'pFabric (LowBDP)', 'pFabric (LowBDP/DumbCore)'], 
        xAxis=[0.099, max(x)], 
        yAxis=[0, max(avg_fct_low_bdp_dumb_core_all)], 
        outputFile="Figure7AllFlows_Avg")
  plotter.PlotN([x, x, x, x], 
  		[avg_fct_ideal_large, avg_fct_pfabric_large, avg_fct_low_bdp_large, avg_fct_low_bdp_dumb_core_large], 
        YTitle='Ratio of Avg FCT', XTitle='Load',
        labels=['Ideal', 'pFabric (Orig)', 'pFabric (LowBDP)', 'pFabric (LowBDP/DumbCore)'], 
        xAxis=[0.099, max(x)], 
        yAxis=[0, max(avg_fct_low_bdp_dumb_core_large)], 
        outputFile="Figure8LargeFlows_Avg")


if __name__ == '__main__':
    main()
