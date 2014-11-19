import sys
from task import *




def main(argv):
  trace = open("../ramdisk/16_17_SortedStart.txt")
  output = open("onejob.txt","w")

  recs = []

  for line in trace:
    task = Task(line)
    if not task.rec_type in recs:
      recs.append(task.rec_type)

  print recs

  trace.close()
  output.close()





if __name__ == "__main__":
  main(sys.argv[1:])
