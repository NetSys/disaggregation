import sys
f = open(sys.argv[1]).readlines()[4:-3]
for x in f:
  id = x.split()[0]
  size = x.split()[9]
  src = x.split()[-3]
  dst = x.split()[-2]
  fct = float(x.split()[5])
  norm = float(x.split()[8])
  print id, size, src, dst, fct, fct / norm, norm
print open(sys.argv[1]).readlines()[-2],
