import sys
sys.path.insert(0, '../../')
import numpy

import parse_ns2_trace as parse
import ideal as ideal


def main():
  loads = ['0.8Load_xxlarge']#, '0.8_xlarge']
  for l in loads:
    print "calculating on", l, "load"
    f = open("./Dataset/flow_"+str(l)+".tr").readlines()[:-1]
    #Flow info is array: [size fct oracle_fct norm_fct]
    print "Read"
    ideal_fct = ideal.get_ideal_fcts(f, 2.5)
    print "Computed"
    out = open("./Dataset/ideal_"+str(l)+"_redone.txt", "w")
    for fct in ideal_fct:
      out.write(str(fct)+'\n')
    print "finish", l



if __name__ == '__main__':
    main()
