#!/usr/bin/python

import sys
import subprocess
import threading

from make_flow_traces import maketrace

'''

ideal usage:

    python ideal.py <trace> 0 0 10

'''

def run_ideal(trace):
    outputname = 'ideal_' + '_'.join(trace.split('_')[1:])
    with open(outputname, 'w') as output:
        output = subprocess.call(['python', '../ideal.py', trace, '0', '0', '10'], stdout = output)

def maketrace_and_run(result, semaphore):
    sempahore.acquire()
    tracename = maketrace(result)
    print result
    run_ideal(tracename)
    semaphore.release()

if __name__ == '__main__':
    if (sys.argv < 2):
        print 'not enough args!'
    else:
        results = sys.argv[1:]
        sempahore = threading.Semaphore(32)
        threads = [threading.Thread(target = maketrace_and_run, args = (r, sempahore)) for r in results]
        [t.start() for t in threads]
        [t.join() for t in threads]
