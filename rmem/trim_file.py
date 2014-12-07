import sys
#sizes = [64, 128, 256, 512, 1024, 2048, 3072, 4096, 1024 * 5, 1024 * 6]
#sizes = [ 1024 * 20, 1024 * 30]
sizes = [1024 * 7, 1024 * 8, 1024 * 9, 1024 * 10]

for size in sizes:
  #size = int(sys.argv[1]) * 1024 * 1024

  size_in_bytes = size * 1024 * 1024
  f = open("../../data/wordcount/wiki1.txt")
  o = open("../../data/wordcount/f" + str(size) + ".txt", "w")
  count = 0
  for l in f:
    o.write(l)
    count += len(l)
    if count > size_in_bytes:
      break

  f.close()
  o.close()


