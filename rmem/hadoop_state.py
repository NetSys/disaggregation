import sys
import os
import time

verbose="-v" in sys.argv
is_reduce = False
os.system("rm .hadoop_info/*")
os.system("echo 0 > /proc/sys/fs/rmem/overflow")
os.system("echo 0 > /proc/sys/fs/rmem/read_bytes")
os.system("echo 0 > /proc/sys/fs/rmem/write_bytes")
os.system("echo 0 > /proc/sys/fs/rmem/line_count")

start_time = time.strftime("%y%m%d%H%M%S",time.localtime())
os.system("echo " + str(start_time) + " > .hadoop_info/start_time")

while True:
  line = sys.stdin.readline()
  if line == "":
    break
  if not is_reduce and "INFO reduce." in line:
    is_reduce = True
    os.system("cat /proc/sys/fs/rmem/read_bytes > .hadoop_info/map_read")
    os.system("cat /proc/sys/fs/rmem/write_bytes > .hadoop_info/map_write")
    map_end_time = time.strftime("%y%m%d%H%M%S",time.localtime())
    os.system("echo " + str(map_end_time) + " > .hadoop_info/map_end_time")
    if verbose:
      sys.stderr.write("================================================\n")
  if verbose:
    sys.stderr.write("~" + line)

  if is_reduce and "Reduce shuffle bytes" in line:
    shuffle_bytes = int(line.strip().replace("Reduce shuffle bytes=",""))
    os.system("echo " + str(shuffle_bytes) + " > .hadoop_info/red_input_bytes")

time.sleep(5)

os.system("cat /proc/sys/fs/rmem/version > .hadoop_info/version")
os.system("cat /proc/sys/fs/rmem/overflow > .hadoop_info/overflow")
os.system("cat /proc/sys/fs/rmem/read_bytes > .hadoop_info/total_read")
os.system("cat /proc/sys/fs/rmem/write_bytes > .hadoop_info/total_write")
os.system("cat /proc/sys/fs/rmem/line_count > .hadoop_info/line_count")

end_time = time.strftime("%y%m%d%H%M%S",time.localtime())
os.system("echo " + str(end_time) + " > .hadoop_info/end_time")


files = os.listdir(".hadoop_info")
results = {}
results["map_read"] = -1
results["map_write"] = -1
results["map_end_time"] = 0
for f in files:
  fh = open(".hadoop_info/" + f)
  results[f] = fh.read().strip()

results["reduce_read"] = str(int(results["total_read"]) - int(results["map_read"]))
results["reduce_write"] = str(int(results["total_write"]) - int(results["map_write"]))

print "ver:", results["version"], "of:", results["overflow"], "mapr:", results["map_read"], \
      "mapw:", results["map_write"], "redr:", results["reduce_read"], "redw:", results["reduce_write"], \
      "red_input", results["red_input_bytes"], \
      "linecount:", results["line_count"], "start", results["start_time"], "mapend:", results["map_end_time"],\
      "end", results["end_time"]

 
