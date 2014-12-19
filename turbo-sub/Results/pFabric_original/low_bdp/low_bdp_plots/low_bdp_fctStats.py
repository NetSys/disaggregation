import sys
sys.path.insert(0, '../../')
import numpy

import parse_ns2_trace as parse
import ideal as ideal

path = '/mnt/akshay/Turbo/NS2/ns-allinone-2.34/ns-2.34/lowbdp_'
gautampath = '/mnt/gautamk/Turbo/NS2/ns-allinone-2.34/ns-2.34/experiments/'

RTOS = [2,5,10,20]
queueSizes = [3,4,5,6]
loads = [0.6]

def meanFlows(flows):
    #returns (allFCT, allSlowdown, largeFCT, largeSlowdown)
    fcts = lambda f: [float(x[1]) for x in f]
    norms = lambda f: [float(x[-1]) for x in f]
    oracles = lambda f: [float(x[-2]) for x in f]

    flows_all = parse.get_flow_info(flows, 0, False)
    # flows is [size, fct, oracle_fct, norm_fct]
    large_threshold = 10000000
    flows_large = [x for x in flows_all if x[0] >= large_threshold]
    
    return ((sum(fcts(flows_all))/sum(oracles(flows_all))), numpy.mean(norms(flows_all)), (sum(fcts(flows_large))/sum(oracles(flows_large))), numpy.mean(norms(flows_large)))

results = {}
for l in loads:
    results[l] = {}
    for r in RTOS:
        results[l][r] = {'allFCT':[], 'largeFCT':[], 'allSlowdown':[], 'largeSlowdown':[]}
        for s in queueSizes:
            #akshay's naming
            currPath = path+str(l)+'_'+str(r)+'_'+str(s)
            #gautam's naming
            #currPath = path+str(s)+'_'+str(r)+'_'+str(l)
            
            flows = open(currPath+'/flow.tr').readlines()
            res = meanFlows(flows)
            results[l][r]['allFCT'].append(res[0])
            results[l][r]['allSlowdown'].append(res[1])
            results[l][r]['largeFCT'].append(res[2])
            results[l][r]['largeSlowdown'].append(res[3])

allFCT = open('low_bdp_allFCT_'+str(loads[0])+'.txt','w')
allSlowdown = open('low_bdp_allSlowdown_'+str(loads[0])+'.txt','w')
largeFCT = open('low_bdp_largeFCT_'+str(loads[0])+'.txt','w')
largeSlowdown = open('low_bdp_largeSlowdown_'+str(loads[0])+'.txt','w')
for load in results:
    for RTO in results[load]:
        [out.write(str(load)+' '+str(RTO)+' ') for out in (allFCT,allSlowdown,largeFCT, largeSlowdown)]
        for dp in results[load][RTO]['allFCT']:
            allFCT.write(str(dp)+' ')
        for dp in results[load][RTO]['allSlowdown']:
            allSlowdown.write(str(dp)+' ')
        for dp in results[load][RTO]['largeFCT']:
            largeFCT.write(str(dp)+' ')
        for dp in results[load][RTO]['largeSlowdown']:
            largeSlowdown.write(str(dp)+' ')
        [out.write('\n') for out in (allFCT,allSlowdown,largeFCT, largeSlowdown)]
