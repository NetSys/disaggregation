## numpy is used for creating fake data
import numpy as np 
import sys

import matplotlib.pyplot as plt

x = ["1us", "5us", "10us",  "20us", "40us", "60us",  "80us", "100us"]
y = [625.6844411, 669.2485921, 680.853924, 719.8754759, 751.0070231, 871.270371, 922.1313169, 1010.919324]
y = [r/y[0] for r in y]
x_ticks = np.arange(0, len(y)) + 1


fig = plt.figure(1, figsize=(8,6))
ax = fig.add_subplot(111)
bp = ax.bar(x_ticks, y, 0.5, align='center')
ax.set_xticks(x_ticks)
ax.set_xticklabels(x)


plt.ylabel("Normalized Application Performance")
#plt.title(sys.argv[0])
plt.savefig(sys.argv[0].replace(".py", ".png"))
plt.savefig(sys.argv[0].replace(".py", ".eps"))
plt.show()
