from cluster import *
import datetime
import math
import sys



def get_time_range(c):
  print "get_time_range Version", 2
  begin_time = int((datetime.datetime(2010, 10, 16,1,0,0) - datetime.datetime(1970, 1, 1)).total_seconds()*1000)
  end_time = int((datetime.datetime(2010, 10, 16,1,1,0) - datetime.datetime(1970, 1, 1)).total_seconds()*1000)

  file = open("../../ramdisk/1min.txt","w")

  for job in c.jobs.itervalues():
    if job.start_time >= begin_time and job.start_time < end_time:
      for task in job.tasks.itervalues():
        file.write(task.line)

  file.close()




def main(argv):
  c = Cluster("../../ramdisk/1h.txt")
  get_time_range(c)

if __name__ == "__main__":
  main(sys.argv[1:])


