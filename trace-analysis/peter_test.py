import sys
import os
import parse_logs
import matplotlib.pyplot as plt




def main(argv):
  dir = "../spark_trace/tpcds_disk/"
  files = os.listdir(dir)
  inputs = []
  outputs = []
  reads = []
  writes = []
  for file in files:
    if not file.startswith('._') and not os.path.isdir(dir + file):
      i,o,r,w = getIOSize(dir + file)
      inputs = inputs + i
      outputs = outputs + o
      reads = reads + r
      writes = writes + w

  fig = plt.figure()
  fig.suptitle(dir)

  plt.subplot(2,2,1)
  if not inputs == []:
    plt.xlabel("Disk Read (MB)")
    plt.ylabel("Count")
    plt.hist(inputs, bins = 50)

  plt.subplot(2,2,2)
  if not outputs == []:
    plt.xlabel("Disk Write (MB)")
    plt.ylabel("Count")
    plt.hist(outputs, bins = 50)

  plt.subplot(2,2,3)
  if not reads == []:
    plt.xlabel("Memory Read (MB)")
    plt.ylabel("Count")
    plt.hist(reads, bins = 50)

  plt.subplot(2,2,4)
  if not writes == []:
    plt.xlabel("Memory Write (MB)")
    plt.ylabel("Count")
    plt.hist(writes, bins = 50)

  plt.show()




def getIOSize(filename):
  print "analysing", filename
  inputSize = []
  outputSize = []
  readSize = []
  writeSize = []

  analyzer = parse_logs.Analyzer(filename)


  for stage in analyzer.stages.values():
    for task in stage.tasks:
      #print "start_time", task.start_time, "stage_id", task.stage_id, "output_mb", task.output_mb, "input_read_method", task.input_read_method, \
      #      "input_mb",task.input_mb, "data_local", task.data_local
      if task.input_mb > 0:
        inputSize.append(task.input_mb)
      if task.output_mb > 0:
        outputSize.append(task.output_mb)
      if hasattr(task, 'remote_mb_read') and task.remote_mb_read > 0:
        readSize.append(task.remote_mb_read)
      if hasattr(task, 'shuffle_mb_written') and task.shuffle_mb_written > 0:
        writeSize.append(task.shuffle_mb_written)


  return inputSize,outputSize,readSize,writeSize

if __name__ == "__main__":
  main(sys.argv[1:])
