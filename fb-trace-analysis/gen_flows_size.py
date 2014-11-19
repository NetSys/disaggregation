from cluster import *
from lib import *
import random
import math
import sys
from gen_flows import *




def gen_flows_size(fileanme = "../ramdisk/sortedflows.txt"):
  print "gen_flows_size Version", 2
  flows = open(fileanme)
  flow_size = {}
  name_dict = {"file_read":0,
               "file_written":1,
               "Map_file_write":2,
               "hdfs_read": 3,
               "hdfs_written_local": 4,
               "hdfs_written_remote1":5,
               "hdfs_written_remote2":5
               }
  count = 0
  for record in flows:
    f = Flow_record.from_str(record)
    flowSizeKey = int(round(pow(10,round(math.log10(f.size),1)),0))
    if flowSizeKey not in flow_size:
      flow_size[flowSizeKey] = [0,0,0,0,0,0]
    flow_size[flowSizeKey][name_dict[f.rec_type]] += 1

    if count % 1000000 == 0:
      print "Finished", count
    count += 1

  flows.close()

  for fsize in sorted(flow_size):
    print fsize, " ".join(map(str,flow_size[fsize]))






def main(argv):
  gen_flows_size()

if __name__ == "__main__":
  main(sys.argv[1:])


