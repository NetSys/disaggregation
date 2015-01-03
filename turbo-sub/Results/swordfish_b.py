# swordfish algorithm

import sys
import bisect
from munkres import Munkres, print_matrix

def remaining_time(flow):
    host_delay = flow['host delay']
    remaining_size = flow['remaining size']
    bandwidth = flow['bandwidth']
    t = 4*host_delay + remaining_size/bandwidth
    return t


def schedule(flows, waiting_flow_ids, running_flow_ids, ibusy, ebusy, time, events, events_time, host_delay):
    def suspend(flow):
        if flow:
            flow['remaining size'] -= (time - flow['updated time']) * flow['bandwidth']
            flow['updated time'] = time
            flow['state'] = 'suspended'
            ibusy[flow['src']] = (False, None)
            ebusy[flow['dest']] = (False, None)
            index = events.index({'flow id': flow['id'], 'type': 'finish', 'time': flow['finish time']})
            del events[index]
            del events_time[index]
            if flow['id'] in waiting_flow_ids:
                raise Exception()
            waiting_flow_ids.append(flow['id'])
            

    # suspend all running flows
    for flow_id in running_flow_ids:
        flow = flows[flow_id]
        if flow['state'] != "started":
            raise Exception("Some flow slipped in!")
        suspend(flow)
    del running_flow_ids[:]

    graph = {}
    flow_id_map = {}
    srcs = []
    dests = []
    for flow_id in waiting_flow_ids:
        src = flows[flow_id]['src']
        dest = flows[flow_id]['dest']
        if src not in graph:
            graph[src] = []
        if dest not in graph[src]:
            graph[src].append(dest)
        if (src, dest) not in flow_id_map:
            flow_id_map[(src, dest)] = []
        flow_id_map[(src, dest)].append(flow_id)
        srcs.append(src)
        dests.append(dest)

    remain_size_f = lambda x: flows[x]['remaining size'] if x >= 0 else 1e10 # 1e10 is assumed to be maximum number
    min_flow_f = lambda x: min(flow_id_map.get(x, [-1]), key = remain_size_f)
    srcs = tuple(set(srcs))
    dests = tuple(set(dests))
    src_n = len(srcs)
    dest_n = len(dests)
    matrix = [[remain_size_f(min_flow_f((srcs[src_i], dests[dest_i]))) for dest_i in range(dest_n)] for src_i in range(src_n)]
    # print matrix

    if not matrix:
        return

    m = Munkres()
    indexes = m.compute(matrix)

    for src_i, dest_i in indexes:
        if matrix[src_i][dest_i] == 1e10:
            continue
        src = srcs[src_i]
        dest = dests[dest_i]
        flow_id = min_flow_f((src, dest))
        flow = flows[flow_id]
        if (flow['src'] != src) or (flow['dest'] != dest):
            raise Exception("Flow on strike!")
        if flow['state'] != 'created' and flow['state'] != 'suspended':
            print flow
            raise Exception("Flow on strike!")
        if ibusy[src][0] or ebusy[dest][0]:
            print ibusy[src], ebusy[dest], flow
            raise Exception("Port is working overtime!")

        ibusy[src] = (True, flow_id)
        ebusy[dest] = (True, flow_id)
        d = remaining_time(flow)
        finish_time = time + d
        idx = bisect.bisect_left(events_time, finish_time)
        events_time.insert(idx, finish_time)
        events.insert(idx, {'flow id': flow_id, 'type': 'finish', 'time': finish_time})
        flow['state'] = 'started'
        flow['updated time'] = time
        flow['finish time'] = finish_time
        waiting_flow_ids.remove(flow_id)
        running_flow_ids.append(flow_id)


def swordfish_b(flows, host_delay, pod_size=16, pod_num=9):
    '''
    Args:
        flows: {start time, size in 1460-byte packet, dutation time, blah, src node id, dest node id]
    '''
    waiting_flow_ids = []
    running_flow_ids = []

    events = [
                 {
                     'flow id': k,
                     'type': 'create', # create, finish
                     'time': v['create time']
                 }
                 for k, v in flows.iteritems()
             ]
    events.sort(key=lambda x: x['time'])
    events_time = [x['time'] for x in events]
    
    ibusy = [(False, None)] * pod_size * pod_num # [(busy, occupying flow id)]
    ebusy = [(False, None)] * pod_size * pod_num
    
    time = 0

    while events:
        e = events[0]
        del events[0]
        del events_time[0]
        time = e['time']
        flow_id = e['flow id']
        if e['type'] == 'create':
            flows[flow_id]['state'] = 'created'
            flows[flow_id]['updated time'] = time
            waiting_flow_ids.append(flow_id)
        elif e['type'] == 'finish':
            iport = flows[flow_id]['src']
            eport = flows[flow_id]['dest']
            if ibusy[iport] != (True, flow_id) or ebusy[eport] != (True, flow_id):
                print ibusy[iport]
                print ebusy[eport]
                print flow_id
                print flows[flow_id]
                raise Exception("Ports on strike!")
            ibusy[iport] = (False, None)
            ebusy[eport] = (False, None)
            flows[flow_id]['state'] = 'finished'
            flows[flow_id]['finish time'] = time
            flows[flow_id]['ideal fct'] = flows[flow_id]['finish time'] - flows[flow_id]['create time']
            flows[flow_id]['updated time'] = time
            running_flow_ids.remove(flow_id)
            print "flow done:", flow_id
            # print flows[flow_id]

        schedule(flows, waiting_flow_ids, running_flow_ids, ibusy, ebusy, time, events, events_time, host_delay)
        #TODO
        #events.sort(key=lambda x: x['time'])


def get_swordfish_b_fcts(lines, host_delay):
    # lines: [start time, stop time, packet size, duration, blah, src, dest]
    flows = {
                i: {
                    'id': i,
                    'create time': float(lines[i].split(' ')[0]) * (10**6), # in us
                    'size': float(lines[i].split(' ')[2]) * 1460 * 8, # in bits
                    'pfabric fct': float(lines[i].split(' ')[3]) * (10**6), # in us
                    'src': int(lines[i].split(' ')[5]),
                    'dest': int(lines[i].split(' ')[6]),
                    'remaining size': float(lines[i].split(' ')[2]) * 1460 * 8, # in bits
                    'state': 'uncreated', # uncreated, created, started, suspended, finished
                    'finish time': None, # in us
                    'ideal fct': None, # in us
                    'updated time': None, # in us
                    'host delay': host_delay, # host delay for the flow in us
                    'bandwidth': 10000, # bandwidth reserved for this flow in bits/us
                }
                for i in range(len(lines))
            }

    swordfish_b(flows, host_delay)
    swordfish_b_fcts = [flows[i]['ideal fct'] for i in range(len(flows))]
    return swordfish_b_fcts


if __name__ == '__main__':
    rv = get_swordfish_b_fcts(open('reproduce_figure8/Dataset/flow_0.2Load.tr').readlines(), 2.5)
