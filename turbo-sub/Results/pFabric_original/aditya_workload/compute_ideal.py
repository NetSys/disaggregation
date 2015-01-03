import sys
sys.path.insert(0, '..')
import numpy

import parse_trace as parse
import ideal as ideal


def main():
    loads = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]

    for l in loads:
        print "calculating on", l, "load"
        f = open("./Dataset/pfabric_aditya_"+str(l)+".tr").readlines()
        #Flow info is array: [size fct oracle_fct norm_fct]
        ideal_fct = ideal.get_ideal_fcts(f, 2.5)
        out = open("./Dataset/ideal_aditya_"+str(l)+".txt", "w")
        for fct in ideal_fct:
            out.write(str(fct)+'\n')
        print "finish", l



if __name__ == '__main__':
    main()
