import sys
sys.path.insert(0, '../../')
import numpy
import plotter

import parse_ns2_trace as parse
import ideal as ideal

def main():
  probe_counts = [5, 10, 100]
  norm_fct_ideal_all = []
  norm_fct_pfabric_all = []

  norm_avg_fct_ideal_all = []
  norm_avg_fct_pfabric_all = []

  norm_fct_ideal_large = []
  norm_fct_pfabric_large = []

  norm_avg_fct_ideal_large = []
  norm_avg_fct_pfabric_large = []

  for pc in probe_counts:
    print "Probe Count: ", pc
    f = open("./Dataset/pF_"+str(pc)+"Probe.tr").readlines()
    #Flow info is array: [size fct oracle_fct norm_fct]
    flow_info = parse.get_flow_info_new(f, 0) #Dictionary with indices as keys
    norm_fct_pfabric_all.append(numpy.mean([x[3] for x in flow_info]))
    norm_avg_fct_pfabric_all.append(numpy.mean([x[1] for x in flow_info]) / 
                                  numpy.mean([x[2] for x in flow_info]))

    large_indices = [i for i in range(len(flow_info)) if flow_info[i][0] >= 100000] #1MB
    large_flow_info = [flow_info[i] for i in large_indices]
    norm_fct_pfabric_large.append(numpy.mean([x[3] for x in large_flow_info]))
    norm_avg_fct_pfabric_large.append(numpy.mean([x[1] for x in large_flow_info]) / 
                                  numpy.mean([x[2] for x in large_flow_info]))
  print "All flows"
  print norm_fct_pfabric_all, norm_avg_fct_pfabric_all
  print "Large flows"
  print norm_fct_pfabric_large, norm_avg_fct_pfabric_large

main()