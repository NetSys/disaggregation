# swordfish algorithm

import sys
import bisect

def remaining_time(flow):
    host_delay = flow['host delay']
    remaining_size = flow['remaining size']
    bandwidth = flow['bandwidth']
    t = 4*host_delay + remaining_size/bandwidth
    return t

finish_flow_cnt = 0

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

    for flow_id in sorted(waiting_flow_ids, key=lambda x: flows[x]['remaining size']):
        flow = flows[flow_id]
        iport = flow['src']
        eport = flow['dest']
        run = False
        if flow['state'] == 'created' or flow['state'] == 'suspended':
            if not ibusy[iport][0] and not ebusy[eport][0]:
                run = True

            if run:
                ibusy[iport] = (True, flow_id)
                ebusy[eport] = (True, flow_id)
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
        else:
            raise Exception("Flow on strike!")


def ideal_cascade(flows, host_delay, pod_size=16, pod_num=9):
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
    
    num_finished = 0
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
            num_finished += 1
            if num_finished % 100000 == 0:
              print "Finished", num_finished

            running_flow_ids.remove(flow_id)
            global finish_flow_cnt
            finish_flow_cnt += 1
            if (finish_flow_cnt % 10000) == 0:
                print "# flow done:", finish_flow_cnt
            # print flows[flow_id]

        schedule(flows, waiting_flow_ids, running_flow_ids, ibusy, ebusy, time, events, events_time, host_delay)
        #TODO
        #events.sort(key=lambda x: x['time'])


def get_ideal_cascade_fcts(lines, host_delay):
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

    ideal_cascade(flows, host_delay)
    ideal_cascade_fcts = [flows[i]['ideal fct'] for i in range(len(flows))]
    return ideal_cascade_fcts


if __name__ == '__main__':
    rv = get_ideal_cascade_fcts(open('./pFabric_original/reproduce_figure8/Dataset/flow_0.2Load.tr').readlines(), 2.5)
