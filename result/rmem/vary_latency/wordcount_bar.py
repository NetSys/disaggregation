## numpy is used for creating fake data
import numpy as np 
import sys

import matplotlib.pyplot as plt

x = ["Local", "1ns\n100Gbps", "1ns\n40Gbps", "1ns\n10Gbps",  "5ns\n100Gbps", "5ns\n40Gbps", "5ns\n10Gbps",  "10ns\n100Gbps", "10ns\n40Gbps", "10ns\n10Gbps"]
y = [319.412226, 328.3559082, 321.8467331, 405.508188, 367.4223788, 363.2763009, 468.4379392, 440.355577, 390.6931932, 507.5296459]
x_ticks = np.arange(0, len(y)) + 1


fig = plt.figure(1, figsize=(16,12))
ax = fig.add_subplot(111)
bp = ax.bar(x_ticks, y, 0.5, align='center')
ax.set_xticks(x_ticks)
ax.set_xticklabels(x)


plt.ylabel("Application Runtime (s)")
plt.title(sys.argv[0])
plt.savefig(sys.argv[0].replace(".py", ".png"))
plt.show()
