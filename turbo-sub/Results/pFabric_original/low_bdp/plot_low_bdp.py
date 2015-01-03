import sys
sys.path.insert(0, '../../')
import numpy
import plotter

import parse_ns2_trace as parse
import ideal as ideal

def main():
  loads = ['medium']

  #Slow Down metric 
  for l in loads:
    norm_fct_ideal_all = []
    norm_fct_pfabric_all = []
    norm_fct_ideal_large = []
    norm_fct_pfabric_large = []
  
    #Avg FCT metric
    avg_fct_ideal_all = []
    avg_fct_pfabric_all = []
    avg_fct_ideal_large = []
    avg_fct_pfabric_large = []

    norm_perc99_short_pf = []
    norm_perc99_short_id = []

    print "Load: ", l
    #Flow info is array: [size fct oracle_fct norm_fct]
    pf_info = parse.get_flow_info(open("./Dataset/pF_noHDelay_0.8_3PktBuffer_" + str(l) + ".tr").readlines(), 0, True)
    sizes = [float(x.split()[0]) for x in open("./Dataset/ideal_noHDelay_0.8_" + str(l) + ".tr").readlines()]
    sizes_pf = [x[0] for x in pf_info]
    pf_fct = [x[1] for x in pf_info]
    ideal_fct = [float(x.split()[1]) for x in open("./Dataset/ideal_noHDelay_0.8_" + str(l) + ".tr").readlines()]
    oracle_fct = [float(x.split()[2]) for x in open("./Dataset/ideal_noHDelay_0.8_" + str(l) + ".tr").readlines()]
    #oracle_fct = [x[2] for x in pf_info];
    norm_pf = [x[3] for x in pf_info]
    norm_id = [x / y for x, y in zip(ideal_fct, oracle_fct)]

    norm_fct_ideal_all.append(numpy.mean(norm_id))
    avg_fct_ideal_all.append(sum(ideal_fct) / sum(oracle_fct))

    norm_fct_pfabric_all.append(numpy.mean(norm_pf))
    avg_fct_pfabric_all.append(sum(pf_fct) / sum(oracle_fct))

    #Large flows for pf and ideal
    large_indices = [i for i in range(len(sizes)) if sizes[i] >= 10000000]
    large_indices_pf = [i for i in range(len(sizes)) if sizes_pf[i] >= 10000000]
    large_ideal_fct = [ideal_fct[i] for i in large_indices]
    large_pf_fct = [pf_fct[i] for i in large_indices_pf]
    large_oracle_fct = [oracle_fct[i] for i in large_indices]
    norm_fct_ideal_large.append(numpy.mean([x / y for x, y in zip(large_ideal_fct, large_oracle_fct)]))
    avg_fct_ideal_large.append(sum(large_ideal_fct) / sum(large_oracle_fct))

    norm_fct_pfabric_large.append(numpy.mean([x / y for x, y in zip(large_pf_fct, large_oracle_fct)]))
    avg_fct_pfabric_large.append(sum(large_pf_fct) / sum(large_oracle_fct))
 
    small_indices = [i for i in range(len(sizes)) if sizes[i] <= 100000]
    print len(small_indices)
    num_small = len(small_indices)
    norm_pf_small_sorted = sorted([norm_pf[i] for i in small_indices])
    norm_id_small_sorted = sorted([norm_id[i] for i in small_indices])

    print norm_fct_ideal_all, norm_fct_pfabric_all, norm_fct_ideal_large, norm_fct_pfabric_large
    print avg_fct_ideal_all, avg_fct_pfabric_all, avg_fct_ideal_large, avg_fct_pfabric_large
    print norm_id_small_sorted[990 * num_small/1000], norm_pf_small_sorted[990 * num_small/1000]

if __name__ == '__main__':
    main()
