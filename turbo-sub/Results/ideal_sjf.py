# ideal algorithm

import sys
import bisect


def transmitted_size(flow, time):
    host_delay = flow['host delay']
    remaining_size = flow['remaining size']
    hop_count = flow['hop count']
    hop_delay = flow['hop delay']
    low_bw = flow['low bandwidth']
    high_bw = flow['high bandwidth']

    elapsed_time = (time - flow['updated time'])
    if elapsed_time < 0:
        raise Exception('Time Distortion!')
    tx_size = elapsed_time * low_bw
    """
    if hop_count == 2:
        tx_size = (elapsed_time - 4*host_delay - 2*hop_count*hop_delay)*low_bw - 1460.0*8
    elif hop_count == 4:
        tx_size = (elapsed_time - 4*host_delay - 2*hop_count*hop_delay - 2*1460.0*8.0/high_bw)*low_bw - 1460.0*8
    else:
        raise Exception('Hop got changed!')
    """
    return tx_size


# Store And Forward 
def remaining_time(flow, cut_through):
    host_delay = flow['host delay']
    remaining_size = flow['remaining size']
    hop_count = flow['hop count']
    hop_delay = flow['hop delay']
    low_bw = flow['low bandwidth']
    high_bw = flow['high bandwidth']

    pd = 4*host_delay + 2*hop_count*hop_delay
    if cut_through == True:
        td = (remaining_size + 40.0*8)/low_bw
        td += 2*40.0*8.0/high_bw if hop_count == 4 else 0
    else:
        td = (remaining_size + 1460.0*8)/low_bw
        td += 2*1460.0*8.0/high_bw if hop_count == 4 else 0

    return pd+td


def schedule(flows, waiting_flows_id, waiting_flow_size, ibusy, ebusy, time, events, events_time, host_delay, cut_through):
    waiting_flows_id_copy = waiting_flows_id[:]
    for flow_id in waiting_flows_id_copy: # waiting_flows_id is sorted by remaining size
        flow = flows[flow_id]
        iport = flow['src']
        eport = flow['dest']
        run = False
        if flow['state'] == 'created' or flow['state'] == 'suspended':
            if not ibusy[iport][0] and not ebusy[eport][0]:
                run = True
            else:
                flow1 = flows.get(ibusy[iport][1])
                flow2 = flows.get(ebusy[eport][1])
                size1 = flow1['size'] if flow1 else float('Inf')
                size2 = flow2['size'] if flow2 else float('Inf')
                if flow['size'] < size1 and flow['size'] < size2:
                    run = True
                    def suspend(flow, waiting_flows_id, waiting_flow_size, time, events, events_time):
                        if flow:
                            flow['remaining size'] -= transmitted_size(flow, time)
                            flow['updated time'] = time
                            flow['state'] = 'suspended'
                            ibusy[flow['src']] = (False, None)
                            ebusy[flow['dest']] = (False, None)
                            index = bisect.bisect_left(events_time, flow['finish time'])
                            if events[index]['flow id'] != flow['id']:
                                print "Id doesn't match", events[index]['flow id'], events[index]['time']
                                index = events.index({'flow id': flow['id'], 'type': 'finish', 'time': flow['finish time']})
                                print "Id doesn't match", events[index]['flow id'], events[index]['time']
                            del events[index]
                            del events_time[index]
                            index = bisect.bisect_left(waiting_flow_size, flow['size'])
                            waiting_flow_size.insert(index, flow['size'])
                            waiting_flows_id.insert(index, flow['id'])
                    suspend(flow1, waiting_flows_id, waiting_flow_size, time, events, events_time)
                    if flow2 != flow1:
                        suspend(flow2, waiting_flows_id, waiting_flow_size, time, events, events_time)

            if run:
                ibusy[iport] = (True, flow_id)
                ebusy[eport] = (True, flow_id)
                d = remaining_time(flow, cut_through)
                finish_time = time + d
                index = bisect.bisect_left(events_time, finish_time)
                events_time.insert(index, finish_time)
                events.insert(index, {'flow id': flow_id, 'type': 'finish', 'time': finish_time})
                flow['state'] = 'started'
                flow['updated time'] = time
                flow['finish time'] = finish_time
                index = waiting_flows_id.index(flow_id)
                del waiting_flow_size[index]
                del waiting_flows_id[index]
        else:
            raise Exception("Flow on strike!")


num_finished = 0


def ideal(flows, host_delay, cut_through, pod_size=16, pod_num=9):
    '''
    Args:
        flows: {start time, size in 1460-byte packet, dutation time, blah, src node id, dest node id]
    '''
    waiting_flows_id = []
    waiting_flow_size = []

    outstanding_events = [
                 {
                     'flow id': k,
                     'type': 'create', # create, finish
                     'time': v['create time']
                 }
                 for k, v in flows.iteritems()
             ]
    outstanding_events.sort(key=lambda x: x['time'])
    outstanding_events_time = [x['time'] for x in outstanding_events]
    
    ibusy = [(False, None)] * pod_size * pod_num # [(busy, occupying flow id)]
    ebusy = [(False, None)] * pod_size * pod_num
    
    time = 0

    events = [outstanding_events.pop(0)]
    events_time = [outstanding_events_time.pop(0)]
    while events:
        e = events[0]
        del events[0]
        del events_time[0]
        time = e['time']
        flow_id = e['flow id']
        if e['type'] == 'create': #Flow created
            flows[flow_id]['state'] = 'created'
            flows[flow_id]['updated time'] = time
            index = bisect.bisect_left(waiting_flow_size, flows[flow_id]['size'])
            waiting_flow_size.insert(index, flows[flow_id]['size'])
            waiting_flows_id.insert(index, flow_id)

            # Add to events
            if len(outstanding_events) > 0:
                nxt_ev = outstanding_events.pop(0)
                nxt_ev_time = outstanding_events_time.pop(0)
                index = bisect.bisect_left(events_time, nxt_ev_time)
                events_time.insert(index, nxt_ev_time)
                events.insert(index, nxt_ev)
        elif e['type'] == 'finish':
            iport = flows[flow_id]['src']
            eport = flows[flow_id]['dest']
            if ibusy[iport] != (True, flow_id) or ebusy[eport] != (True, flow_id):
                raise Exception("Ports on strike!")
            ibusy[iport] = (False, None)
            ebusy[eport] = (False, None)
            flows[flow_id]['state'] = 'finished'
            flows[flow_id]['finish time'] = time
            flows[flow_id]['ideal fct'] = flows[flow_id]['finish time'] - flows[flow_id]['create time']
            flows[flow_id]['updated time'] = time
            global num_finished
            num_finished += 1
            if num_finished % 1000 == 0:
              print "Finished", num_finished

        schedule(flows, waiting_flows_id, waiting_flow_size, ibusy, ebusy, time, events, events_time, host_delay, cut_through)
        #TODO
        #events.sort(key=lambda x: x['time'])


def get_ideal_fcts(lines, host_delay, cut_through=False):
    # lines: [start time, stop time, packet size, duration, blah, src, dest]
    flows = {
                int(lines[i].split()[0]): {
                    'id': int(lines[i].split()[0]),
                    'create time': float(lines[i].split(' ')[1]) * (10**6), # in us
                    'size': float(lines[i].split(' ')[3]) * 1460 * 8, # in bit
                    'pfabric fct': float(lines[i].split(' ')[4]) * (10**6), # in us
                    'src': int(lines[i].split(' ')[6]),
                    'dest': int(lines[i].split(' ')[7]),
                    'remaining size': float(lines[i].split(' ')[3]) * 1460 * 8, # in bit
                    'state': 'uncreated', # uncreated, created, started, suspended, finished
                    'finish time': None, # in us
                    'ideal fct': None, # in us
                    'updated time': None, # in us
                    'host delay': host_delay, # host delay for the flow in us
                    'hop count': 2 if (int(lines[i].split(' ')[6])/16 == int(lines[i].split(' ')[7])/16) else 4, # 16, 2 and 4 hard-coded
                    'hop delay': 0.2, # in us
                    'low bandwidth': 10000, # bandwidth in bits/us
                    'high bandwidth': 40000, # bandwidth in bits/us
                }
                for i in range(len(lines))
            }
    flows = {i:dict(f.items() + {'oracle fct': remaining_time(f, cut_through)}.items()) for i, f in flows.iteritems()}

    ideal(flows, host_delay, cut_through)
    # return value structure: size in byte, ideal FCT in us, oracle FCT in us, normalized FCT, flow id
    ideal_fcts = [(int(flows[i]['size']/8), flows[i]['ideal fct'], flows[i]['oracle fct'], flows[i]['ideal fct']/flows[i]['oracle fct']) for i in range(len(flows))]

    #print flows

 #   import numpy
#    print numpy.mean(ideal_fcts)
    return ideal_fcts


if __name__ == '__main__':
    rv = get_ideal_fcts(open('./pFabric_original/reproduce_figure8/Dataset/flow_0.2Load.tr').readlines(), 2.5)
