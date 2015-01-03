import sys
import os
import time

verbose="-v" in sys.argv

start_time = time.time()
start_time_str = time.strftime("%y%m%d%H%M%S", time.localtime())

while True:
  line = sys.stdin.readline()
  if line == "":
    break
  if verbose:
    sys.stdout.write("~" + line)

end_time = time.time()
end_time_str = time.strftime("%y%m%d%H%M%S", time.localtime())

duration = end_time - start_time

result = "Start: " + start_time_str + " End: " + end_time_str + " Duration: " + str(duration) \
       + " Rmem: " + sys.argv[1] + " Bw: " + sys.argv[2] + " Ltcy: " + sys.argv[3] \
       + " Inj: " + sys.argv[4]
print result
os.system("echo \"" + result + "\" >> ec2_exp_log.txt")

 
