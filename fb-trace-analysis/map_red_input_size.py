from cluster import *
from lib import *
import random
import math
import sys
import numpy as np






def map_red_input_size(u):
  print "map_red_input_size Version:", 23

  large_reduce_count = 0
  large_reduce_with_large_map_count = 0

  next_percent = 0.01
  count = 0
  for job in u.jobs.itervalues():
    for red_task in job.reduce_tasks.itervalues():
      count += 1
      if float(count)/u.total_red_tasks > next_percent:
        print "Finished", next_percent, "(", count, "/", u.total_red_tasks, ")"
        next_percent += 0.01

      if red_task.reduce_shuffle_bytes > 2 * 1024 * 1024 * 1024:
        large_reduce_count += 1


        if not hasattr(job, "has_large_map_task"):
          for map_task in job.map_tasks.itervalues():
            if map_task.map_input_bytes > 2 * 1024 * 1024 * 1024:
              job.has_large_map_task = True
              break
          if not hasattr(job, "has_large_map_task"):
            job.has_large_map_task = False

        if job.has_large_map_task:
          large_reduce_with_large_map_count += 1

  print str(large_reduce_with_large_map_count)+"/" + str(large_reduce_count) + " = " + str(float(large_reduce_with_large_map_count)/large_reduce_count)


def largest_task(u):
  print "largest_task Version:", 2

  dist = np.zeros([11,11], dtype=np.int)

  next_percent = 0.01
  count = 0
  for job in u.jobs.itervalues():
    largest_map = 0
    largest_red = 0
    for task in job.tasks.itervalues():
      count += 1
      if float(count)/u.total_tasks > next_percent:
        print "Finished", next_percent, "(", count, "/", u.total_tasks, ")"
        next_percent += 0.01

      if task.rec_type == "MapAttempt" and task.map_input_bytes > largest_map:
        largest_map = task.map_input_bytes
      if task.rec_type == "ReduceAttempt" and task.reduce_shuffle_bytes > largest_red:
        largest_red = task.reduce_shuffle_bytes
    largest_map_round = largest_map / (1024 * 1024 * 1024)
    largest_red_round = largest_red / (1024 * 1024 * 1024)
    largest_map_round = min(10, largest_map_round)
    largest_red_round = min(10, largest_red_round)
    dist[largest_map_round,largest_red_round] += 1

  print dist






def main(argv):




  u = Cluster("../../ramdisk/24h.txt", get_server_list=False)


  o = map_red_input_size(u)



if __name__ == "__main__" :
  main(sys.argv[1:])


