#141206150652 2549262 512 ver: 5 of: 0 mapr: 0 mapw: 0 redr: 0 redw: 0 red_input 28073830 linecount: 0 start 141206150454 mapend: 141206150644 end 141206150652
import numpy as np
import matplotlib.pyplot as plt
#map input, mapr, mapw, redr, redw, red input
data = np.loadtxt("data.txt", usecols=(2, 8, 10, 12, 14, 16), delimiter=" ")

mapr = np.polyfit(data[:,0]*1024*1024, data[:,1], 1)
mapw = np.polyfit(data[:,0]*1024*1024, data[:,2], 1)
redr = np.polyfit(data[:,5], data[:,3], 1)
redw = np.polyfit(data[:,5], data[:,4], 1)

x = np.array(range(1,11)) * 1024 * 1024 * 1024
y_mapr = x * mapr[0] + mapr[1]
plt.subplot(2,2,1)
plt.plot(data[:,0]*1024*1024, data[:,1], "*", x, y_mapr, "-")
plt.xlabel("Map Input (Bytes)")
plt.ylabel("Remote Read (Bytes)")

y_mapw = x * mapw[0] + mapw[1]
plt.subplot(2,2,2)
plt.plot(data[:,0]*1024*1024, data[:,2], "*", x, y_mapw, "-")
plt.xlabel("Map Input (Bytes)")
plt.ylabel("Remote Write (Bytes)")

x = np.array(range(1,11)) * 1024 * 1024 * 1024 /25
y_redr = x * redr[0] + redr[1]
plt.subplot(2,2,3)
plt.plot(data[:,5], data[:,3], "*", x, y_redr, "-")
plt.xlabel("Reduce Input (Bytes)")
plt.ylabel("Remote Read (Bytes)")


y_redw = x * redw[0] + redw[1]
plt.subplot(2,2,4)
plt.plot(data[:,5], data[:,4], "*", x, y_redw, "-")
plt.xlabel("Reduce Input (Bytes)")
plt.ylabel("Remote Write (Bytes)")


plt.show()

print mapr
print mapw
print redr
print redw
