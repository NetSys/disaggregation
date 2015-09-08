import sys

def process(input_file):
	output_file = input_file.replace(".txt", ".cdf")
	keys = []
	s = 0
	for i in [100000, 10000, 1000, 100, 10, 1]:
	  for j in range(1,10):
	    s += i
	    keys.append(s)
	s += 1
	keys.append(s)


	data = []
	f = open(input_file)
	for l in f:
	  arr = l.split(" ")
	  slow = int(float(arr[0]) * 10000)
	  cdf = int(float(arr[1]) * 1000 * 1000)
	  data.append((slow, cdf))
	f.close()

	result = []
	for key in keys:
	  for d in data:
	    if d[1] >= key:
	      result.append(d)
	      break

	fo = open(output_file, "w")
	[fo.write("%d %d\n" % (r[0], r[1])) for r in sorted(set(result))]
	fo.close()

for s in sys.argv[1:]:
  process(s)
