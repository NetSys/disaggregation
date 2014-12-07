#141206150652 2549262 512 ver: 5 of: 0 mapr: 0 mapw: 0 redr: 0 redw: 0 red_input 28073830 linecount: 0 start 141206150454 mapend: 141206150644 end 141206150652
import numpy as np

#map input, mapr, mapw, redr, redw, red input
data = np.loadtxt("data.txt", usecols=(2, 8, 10, 12, 14, 16), delimiter=" ")

mapr = np.polyfit(data[:,0]*1024*1024, data[:,1], 1)
mapw = np.polyfit(data[:,0]*1024*1024, data[:,2], 1)
redr = np.polyfit(data[:,5], data[:,3], 1)
redw = np.polyfit(data[:,5], data[:,4], 1)
print mapr
print mapw
print redr
print redw
