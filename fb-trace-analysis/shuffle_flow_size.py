from cluster import *
import math
import sys



def get_shuffle_flow_size(u):
  flowSize = {}
  for job in u.jobs.itervalues():
    for task in job.reduce_tasks.itervalues():
      numMapTasks = len(job.map_tasks)
      if numMapTasks > 0:
        if not task.reduce_shuffle_bytes == None and task.reduce_shuffle_bytes > 0:
          shuffleFlowSize = float(task.reduce_shuffle_bytes)/numMapTasks
          flowSizeKey = int(round(pow(10,round(math.log10(shuffleFlowSize),1)),0))
          if not flowSizeKey in flowSize:
            flowSize[flowSizeKey] = 0
          flowSize[flowSizeKey] += numMapTasks

  for size in sorted(flowSize):
    print str(size) + " " + str(flowSize[size])

def main(argv):
  u = Cluster()
  get_shuffle_flow_size(u)

if __name__ == "__main__":
  main(sys.argv[1:])


