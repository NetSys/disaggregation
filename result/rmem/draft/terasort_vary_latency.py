## numpy is used for creating fake data
import numpy as np 
import sys

import matplotlib.pyplot as plt

x = ["1us\n40Gbps", "5us\n40Gbps", "10us\n40Gbps",  "20us\n40Gbps", "40us\n40Gbps", "60us\n40Gbps",  "80us\n40Gbps", "100us\n40Gbps"]
y = [625.6844411, 731.286963, 680.853924, 719.8754759, 751.0070231, 871.270371, 922.1313169, 1010.919324]
x_ticks = np.arange(0, len(y)) + 1


fig = plt.figure(1, figsize=(8,6))
ax = fig.add_subplot(111)
bp = ax.bar(x_ticks, y, 0.5, align='center')
ax.set_xticks(x_ticks)
ax.set_xticklabels(x)


plt.ylabel("Application Runtime (s)")
plt.title(sys.argv[0])
plt.savefig(sys.argv[0].replace(".py", ".png"))
plt.show()
