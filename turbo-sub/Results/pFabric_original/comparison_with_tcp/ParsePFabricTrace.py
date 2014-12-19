import sys
import numpy

def print_statistics(f):
  flow_size = [1460 * float(x.split()[0]) for x in f]
  hops = []
  for x in f:
    s = float(x.split()[3])
    d = float(x.split()[4])
    if (s/16) == (d/16):
      hops.append(2)
    else:
      hops.append(4)

  fct = [1000000 * float(x.split()[1]) for x in f] #fct in us
  oracle_fct = []
  outliers = []
  for i in range(len(f)):
  
  
    pd = 4 * 2.5 + 2 * hops[i] * 0.2 #in us (host delay + switch delay)
    td = (flow_size[i] + 1460)* 8.0 / (10000.0) #us (fs + first)
    if hops[i] == 4:
      td += 2 * 1460.0 * 8.0 / (40000.0)
    oracle_fct.append(pd + td)


  #for x in outliers:
  #  print x
  norm_fct = [x / y for x, y in zip(fct, oracle_fct)]
  norm_fct_big = [norm_fct[i] for i in range(len(norm_fct)) if flow_size[i] >= 10000000]
  print numpy.mean(oracle_fct), numpy.mean(fct), numpy.mean(fct) / numpy.mean(oracle_fct),
  print numpy.mean(norm_fct), numpy.mean(norm_fct_big)

lines = open(sys.argv[1]).readlines()
lines = [x for x in lines if len(x.split()) > 3]
print_statistics(lines)


