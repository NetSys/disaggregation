#!/usr/bin/python

import sys
import csv

# stdin = output of tail -v -n 2 <exps>

def get_results():
    # divide into groups of 3
    currbuffer = []
    for line in sys.stdin:
        if (line == '\n'):
            continue
        currbuffer.append(line)
        if (len(currbuffer) == 3):
            yield currbuffer
            currbuffer = []

def read_exp(exp):
    desc, fct, _ = exp

    desc = desc.split()[1]
    name, load, skew, dist = desc.split('_')

    _, avgfct, _, slowdown = fct.split()
    avgfct, slowdown = map(float, (avgfct, slowdown))

    return (name, load, skew, dist, avgfct, slowdown)


assert(len(sys.argv) == 2)
with open(sys.argv[1], 'w') as f:
    csvwriter = csv.writer(f)
    for exp in get_results():
        csvwriter.writerow(read_exp(exp))
