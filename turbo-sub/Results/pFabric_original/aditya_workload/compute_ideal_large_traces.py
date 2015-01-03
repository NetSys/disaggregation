import sys
sys.path.insert(0, '..')
import numpy

import parse_trace as parse
import ideal_large as ideal


def main():
    loads = ['0.8_large']#, '0.8_xlarge']

    for l in loads:
        print "calculating on", l, "load"
        f = open("./Dataset/pfabric_aditya_"+str(l)+".tr").readlines()
        #Flow info is array: [size fct oracle_fct norm_fct]
        print "Read"
        ideal_fct = ideal.get_ideal_fcts(f, 2.5)
        print "Computed"
        out = open("./Dataset/ideal_aditya_"+str(l)+".txt", "w")
        for fct in ideal_fct:
            out.write(str(fct)+'\n')
        print "finish", l



if __name__ == '__main__':
    main()
