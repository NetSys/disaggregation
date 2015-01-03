from cluster import *
from lib import *
import random
import math
import sys






def shuffle_size(u):
  print "shuffle_size Version:", 1

  total_dist = {}
  total_dist_count = 0
  per_flow_dist = {}
  per_flow_dist_count = 0

  next_percent = 0.01
  count = 0
  for job in u.jobs.itervalues():
    for task in job.tasks.itervalues():
      count += 1
      if float(count)/u.total_tasks > next_percent:
        print "Finished", next_percent, "(", count, "/", u.total_tasks, ")"
        next_percent += 0.01
      if task.rec_type == "ReduceAttempt" and task.reduce_shuffle_bytes and len(job.map_tasks) > 0:
        total_shuffle = task.reduce_shuffle_bytes / 1460 + 1
        per_flow = task.reduce_shuffle_bytes / len(job.map_tasks) / 1460 + 1

        total_shuffle_key = int(round(pow(10,round(math.log10(total_shuffle),1)),0))
        per_flow_key = int(round(pow(10,round(math.log10(per_flow),1)),0))

        if total_shuffle_key not in total_dist:
          total_dist[total_shuffle_key] = 0
        total_dist[total_shuffle_key] += 1
        total_dist_count += 1

        if per_flow_key not in per_flow_dist:
          per_flow_dist[per_flow_key] = 0
        per_flow_dist[per_flow_key] += len(job.map_tasks)
        per_flow_dist_count += len(job.map_tasks)

  print "Shuffle Dist:"
  ss = 0
  for k in sorted(total_dist):
    ss += total_dist[k]
    print k, total_dist[k], float(total_dist[k])/total_dist_count, float(ss)/total_dist_count

  print "Flow Dist:"
  ss = 0
  for k in sorted(per_flow_dist):
    ss += per_flow_dist[k]
    print k, per_flow_dist[k], float(per_flow_dist[k])/per_flow_dist_count, float(ss)/per_flow_dist_count










def main(argv):


  u = Cluster("../../ramdisk/1h.txt", get_server_list = False)


  shuffle_size(u)

if __name__ == "__main__" :
  main(sys.argv[1:])


