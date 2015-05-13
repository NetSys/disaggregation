#!/usr/bin/python

import sys
import subprocess

'''

format should be:

    <id> <start time> 0 <size_pkts> <pfabric fct> 0 <src> <dst>

    0    4            - 1           8             - 2     3

results_pfabric_70short_load0.7_skew0.0_100k.txt
'''

def format_line(linestr):
    line = linestr.split()
    return ' '.join(
        map(
            str,
            (line[0],float(line[4])/1e6, 0, float(line[1])/1460, float(line[8])/1e6, 0, line[2], line[3])
        )
    )

def maketrace(result):
    name = result.split('/')[-1].split('_')
    load = name[3]
    skew = name[-2]
    dist = name[2]
    outname = 'flows_{0}_{1}_{2}'.format(load, skew, dist)
    with open(outname, 'w') as f:
        flows = subprocess.check_output(['egrep', '^[0-9]+ [0-9]+', result])
        flows = flows.split('\n')[:-1]
        flows = map(format_line, flows)
        f.write('\n'.join(flows))
    return outname

if __name__ == '__main__':
    if (len(sys.argv) < 4):
        print 'not enough args?'
    else:
        traces = sys.argv[1:]

        for trace in traces:
            maketrace(trace)
