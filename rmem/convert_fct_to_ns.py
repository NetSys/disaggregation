import sys

#2359296 2030.539

for s in sys.stdin:
  arr = s.split(" ")
  num_page = int(arr[0])/4096
  fct_ns = int(float(arr[1])*1000)
  if num_page < 4096:
    print "%s %s" % (num_page, fct_ns)
