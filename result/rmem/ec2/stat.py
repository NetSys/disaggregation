#141206150652 2549262 512 ver: 5 of: 0 mapr: 0 mapw: 0 redr: 0 redw: 0 red_input 28073830 linecount: 0 start 141206150454 mapend: 141206150644 end 141206150652
import numpy as np
import matplotlib.pyplot as plt
#map input, mapr, mapw, redr, redw, red input
data = np.loadtxt("data.txt", usecols=(5, 9, 11), delimiter=" ")

total = {}
count = {}
for i in range(0, len(data)):
  duration=data[i,0]
  bw=data[i,1]
  ltcy=data[i,2]
  key=str(int(ltcy)) + "-" + str(int(bw/1000000000))
  if key not in total:
    total[key] = 0
    count[key] = 0
  total[key] += duration
  count[key] += 1

for key in sorted(total):
  print key, total[key]/count[key]
