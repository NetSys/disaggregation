import sys
sys.path.insert(0, '../..')
import numpy

import parse_ns2_trace as parse
import swordfish_b as sfb

def main():
    loads = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]

    for l in loads:
        print "calculating on", l, "load"
        f = open("./Dataset/flow_"+str(l)+"Load.tr").readlines()
        #Flow info is array: [size fct oracle_fct norm_fct]
        sfb_fct = sfb.get_swordfish_b_fcts(f, 2.5)
        out = open("./Dataset/swordfish_b_"+str(l)+"Result.txt", "w")
        for fct in sfb_fct:
            out.write(str(fct)+'\n')
        print "finish", l



if __name__ == '__main__':
    main()
