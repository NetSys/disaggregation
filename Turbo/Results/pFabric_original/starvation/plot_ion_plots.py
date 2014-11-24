import sys
sys.path.insert(0, '../..')
import numpy
import random
import parse_ns2_trace as parse
import ideal as ideal



def main():
  loads = ['0.8Load_xlarge']
  for load in loads:
    f = open('Dataset/flow_' + load + '.tr').readlines()
    flow_info = parse.get_flow_info_new(f, 2.5) #Dictionary with indices as keys
    start_times = [float(x.split()[0]) for x in f]
    finish_times = [float(x.split()[1]) for x in f]
    sizes = [float(x.split()[2]) for x in f]
    started = [0] * (int(max(finish_times)) + 1) 
    finished = [0] * (int(max(finish_times)) + 1) 
    avg_size_bins = [0] * (int(max(finish_times)) + 1) 
    size_bins = [0] * (int(max(finish_times)) + 1)
    
    #Compute outstanding bytes
    print numpy.mean(sizes)
    for i in range(len(start_times)):
      started[int(start_times[i])] += sizes[i]
      finished[int(finish_times[i])] += sizes[i]
   
    s = [0] * len(started)
    f = [0] * len(started)
    s[0] = started[0]
    f[0] = finished[0]
    for i in range(1, len(started)):
      s[i] = s[i-1] + started[i]
      f[i] = f[i-1] + finished[i]
    diff = [x - y for x, y in zip(s, f)]
    print diff 
main()
