import sys
sys.path.insert(0, '../..')
import numpy
#import plotter

import parse_ns2_trace as parse
import ideal as ideal

def main():
  f = open(sys.argv[1]).readlines()
  #Flow info is array: [size fct oracle_fct norm_fct]
  #flow_info = parse.get_flow_info_new(f, 2.5) #Dictionary with indices as keys
  ideal_fct = ideal.get_ideal_fcts(f, 0)
  #inorm_fct_ideal = [x / y[2] for x, y in zip(ideal_fct, flow_info)]
  #print numpy.mean(norm_fct_ideal), numpy.mean([x[3] for x in flow_info])
  f2 = open(sys.argv[2], 'w')
  for x in ideal_fct:
    f2.write(str(x) + "\n")
  f2.close()


if __name__ == '__main__':
    main()

