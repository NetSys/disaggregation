import sys
sys.path.insert(0, '../..')
import numpy

import parse_ns2_trace as parse
import ideal_cascade as ideal


def main(load):
    print "calculating on", load, "load"
    f = open("./Dataset/flow_"+str(load)+"Load.tr").readlines()
    #Flow info is array: [size fct oracle_fct norm_fct]
    ideal_cascade_fct = ideal.get_ideal_cascade_fcts(f, 2.5)
    out = open("./Dataset/ideal_cascade_"+str(load)+"Result.txt", "w")
    for fct in ideal_cascade_fct:
        out.write(str(fct)+'\n')
    print "finish", load


if __name__ == '__main__':
    main(sys.argv[1])
