import sys


size_gb = float(sys.argv[2])
size_in_bytes = size_gb * 1024 * 1024 * 1024
o = open(sys.argv[3], "w")

count = 0
while count <= size_in_bytes:
  f = open(sys.argv[1])
  for l in f:
    o.write(l)
    count += len(l)
    if count > size_in_bytes:
      break
  f.close()
o.close()


