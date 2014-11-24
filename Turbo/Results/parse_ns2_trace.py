import sys
import numpy

def get_oracle_fct(flow_size, s, d, host_delay, cut_through, bandwidth):
  num_hops = 4
  if (s/16) == (d/16):
    num_hops = 2
  pd = 4 * host_delay + 2 * num_hops* 0.2 #in us (host delay + switch delay)

  if cut_through == True:
    td = (flow_size + 40)* 8.0 / (bandwidth) #us (fs + first)
  else:
    td = (flow_size + 1460)* 8.0 / (bandwidth)
  if num_hops == 4:
    if cut_through == True:
      td += 2 * 40.0 * 8.0 / (4 * bandwidth)
    else:
      td += 2 * 1460.0 * 8.0 / (4 * bandwidth)
  return (pd + td)



#Format is start_time, finish_time, size, fldur, 0, s, d
#Bandwidth in Mbps
def get_flow_info(lines, host_delay, cut_through=False, bandwidth=10000):
  fcts = [0 for x in range(len(lines))]
  i = 0
  for x in lines:
    id = int(x.split()[0])
    flow_size = 1460 * float(x.split()[3])
    s = int(x.split()[6])
    d = int(x.split()[7])
    start_time = 1000000 * float(x.split()[1])
    finish_time = 1000000 * float(x.split()[2])
    #print "Oracle", flow_size, s, d, host_delay
    oracle_fct = get_oracle_fct(flow_size, s, d, host_delay, cut_through, bandwidth)
    fct = 1000000 * float(x.split()[4]) #fct in us
    norm_fct = fct / oracle_fct
    fcts[id] = [id, flow_size, s, d, start_time, finish_time, fct, oracle_fct, norm_fct]
    i += 1
  return fcts


#Format is start_time, finish_time, size, fldur, 0, s, d
def get_flow_info_new(lines, host_delay, cut_through=False, bandwidth=10000):
  return get_flow_info(lines, host_delay, cut_through, bandwidth);

if __name__ == '__main__':
    if len(sys.argv) < 5:
      print "Usage: <trace> <host_delay> <cut_through> <bandwidth(Gbps)>"
      sys.exit(0)
    lines = open(sys.argv[1]).readlines()
    host_delay = float(sys.argv[2])
    ct = int(sys.argv[3])
    if ct == 1:
      cut_through = True
    else:
      cut_through = False
    bandwidth = 1000 * int(sys.argv[4])
    rv = get_flow_info(lines, host_delay, cut_through, bandwidth)
    for v in rv:
        print v[0], v[1], v[2], v[3], v[4], v[5], v[6], v[7], v[8]
    print "AverageFCT", numpy.mean([x[6] for x in rv]), "MeanSlowdown",\
      numpy.mean([x[8] for x in rv])
