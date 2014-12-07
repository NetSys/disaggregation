import sys
sys.path.insert(0, '../../')
import numpy
# import plotter

import parse_ns2_trace as parse
import ideal as ideal

def main():
  sizes = [3,4,5,6]
  
  for s in sizes:
    print 'queuesize = ', s
    flows_all = parse.get_flow_info(open('./queue'+str(s)+'/flow_100k.tr').readlines(), 0, True)
    # flows is [size, fct, oracle_fct, norm_fct]
    large_threshold = 10000000
    flows_large = [x for x in flows_all if x[0] >= large_threshold]
    
    fcts = lambda f: [float(x[1]) for x in f]
    norms = lambda f: [float(x[-1]) for x in f]
    oracles = lambda f: [float(x[-2]) for x in f]
    
    def print_stats(flows):
        print '\t\tAverage Norm FCT (Mean Slowdown):', numpy.mean(norms(flows))
        print '\t\tNormalized Average FCT:', sum(fcts(flows))/sum(oracles(flows))
    
    print '\tAll Flows'
    print_stats(flows_all)
    
    print '\tLarge Flows'
    print_stats(flows_large)



if __name__ == '__main__':
    main()
