path = '/mnt/gautamk/Turbo/NS2/ns-allinone-2.34/ns-2.34/experiments/' #'../lowbdp_'
flowPath = '/flow.tr'
tlossPath = '/tloss.tr'

RTOS = [2,5,10,20]
queueSizes = [3,4,5,6]
loads = [0.8] #[0.6] #for akshay's load experiments 

def flowTotalPackets(flow):
    return sum(float(x.split()[3]) for x in flow)
    
def droppedPackets(tloss, flow):
    drops = sum(int(x) for x in tloss[0].split())
    return drops/flowTotalPackets(flow)

def deadPackets(tloss, flow):
    dead = sum(int(x) for x in tloss[0].split()[1:])
    return dead/flowTotalPackets(flow)
    
def utilization(tloss, flow):
    #want bston_depart
    byteDepartures = float(tloss[-1].split()[2])
    startTime = float(flow[0].split()[1])
    endTime = float(flow[-1].split()[2])
    numberOfLinks = 16*9
    print((byteDepartures*8)/((endTime-startTime)*numberOfLinks))
    return (byteDepartures*8)/((endTime-startTime)*numberOfLinks)

results = {}
for l in loads:
    results[l] = {}
    for r in RTOS:
        results[l][r] = {'drop':[], 'dead':[], 'util':[]}
        for s in queueSizes:
            #akshay's naming
            #currPath = path+str(l)+'_'+str(r)+'_'+str(s)
            #gautam's naming
            currPath = path+str(s)+'_'+str(r)+'_'+str(l)
            
            flows = open(currPath+flowPath).readlines()
            tloss = open(currPath+tlossPath).readlines()
            results[l][r]['drop'].append(droppedPackets(tloss, flows)*100)
            results[l][r]['dead'].append(deadPackets(tloss, flows)*100)
            results[l][r]['util'].append(utilization(tloss, flows)*100)
            
drop = open('low_bdp_drops_'+str(loads[0])+'.txt','w')
dead = open('low_bdp_dead_'+str(loads[0])+'.txt','w')
util = open('low_bdp_util_'+str(loads[0])+'.txt','w')
for load in results:
    for RTO in results[load]:
        [out.write(str(load)+' '+str(RTO)+' ') for out in (drop,dead,util)]
        for dp in results[load][RTO]['drop']:
            drop.write(str(dp)+' ')
        for dp in results[load][RTO]['dead']:
            dead.write(str(dp)+' ')
        for dp in results[load][RTO]['util']:
            util.write(str(dp)+' ')
        [out.write('\n') for out in (drop,dead,util)]
        