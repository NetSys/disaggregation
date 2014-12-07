import numpy

f = open("log.tr").readlines()


queueDownFromRack = {}
queueDownFromCore = {}

for i in range(144):
  queueDownFromRack[i] = []

for i in range(36):
  queueDownFromCore[i] = []

flowsStart = []
flowsEnd = []
for x in f:
  if 'fin' in x:
    splits = x.split()
    if len(splits) < 6:
      print splits
    source = int(splits[4]); dest = int(splits[5]);
    queueDownFromRack[dest].append([float(splits[1]) - float(splits[9]), float(splits[1])])
    core = (source + dest) % 4
    rack = dest/16
    qid = core + rack * 4
    if source/16 != dest/16:
      queueDownFromCore[qid].append([float(splits[1]) - float(splits[9]), float(splits[1])])




time = 1.7
numConcurrentFromRack = [0 for x in range(144)]
for i in range(144):
  for x in queueDownFromRack[i]:
    start = x[0]; end = x[1];
    if time > start and time < end:
      numConcurrentFromRack[i] += 1

print min(numConcurrentFromRack), max(numConcurrentFromRack), numpy.mean(numConcurrentFromRack)
numConcurrentFromCore = [0 for x in range(36)]
for i in range(36):
  for x in queueDownFromCore[i]:
    start = x[0]; end = x[1];
    if time > start and time < end:
      numConcurrentFromCore[i] += 1

print "\n\n"
print min(numConcurrentFromCore), max(numConcurrentFromCore), numpy.mean(numConcurrentFromCore)
