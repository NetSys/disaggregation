#141206150652 2549262 512 ver: 5 of: 0 mapr: 0 mapw: 0 redr: 0 redw: 0 red_input 28073830 linecount: 0 start 141206150454 mapend: 141206150644 end 141206150652
import numpy as np
import matplotlib.pyplot as plt
#map input, mapr, mapw, redr, redw, red input
data = np.loadtxt("terasort.txt", usecols=(3, 9, 11, 13, 15, 17), delimiter=" ")

mapr = np.polyfit(data[:,0], data[:,1]/(1024*1024), 1)
mapw = np.polyfit(data[:,0], data[:,2]/(1024*1024), 1)
redr = np.polyfit(data[:,5]/(1024*1024), data[:,3]/(1024*1024), 1)
redw = np.polyfit(data[:,5]/(1024*1024), data[:,4]/(1024*1024), 1)

x = np.array(range(1,11)) * 1024
y_mapr = x * mapr[0] + mapr[1]
plt.subplot(2,2,1)
plt.plot(data[:,0], data[:,1]/(1024*1024), "*", x, y_mapr, "-")
plt.xlabel("Map Input (MBytes) %f * x + %f" % (mapr[0], mapr[1]))
plt.ylabel("Remote Read (MBytes)")

y_mapw = x * mapw[0] + mapw[1]
plt.subplot(2,2,2)
plt.plot(data[:,0], data[:,2]/(1024*1024), "*", x, y_mapw, "-")
plt.xlabel("Map Input (MBytes) %f * x + %f" % (mapw[0], mapw[1]))
plt.ylabel("Remote Write (MBytes)")

x = np.array(range(1,11)) * 1024
y_redr = x * redr[0] + redr[1]
plt.subplot(2,2,3)
plt.plot(data[:,5]/(1024*1024), data[:,3]/(1024*1024), "*", x, y_redr, "-")
plt.xlabel("Reduce Input (MBytes) %f * x + %f" % (redr[0], redr[1]))
plt.ylabel("Remote Read (MBytes)")


y_redw = x * redw[0] + redw[1]
plt.subplot(2,2,4)
plt.plot(data[:,5]/(1024*1024), data[:,4]/(1024*1024), "*", x, y_redw, "-")
plt.xlabel("Reduce Input (MBytes) %f * x + %f" % (redw[0], redw[1]))
plt.ylabel("Remote Write (MBytes)")



print mapr
print mapw
print redr
print redw

plt.show()
