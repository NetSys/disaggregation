## numpy is used for creating fake data
import numpy as np 
import sys

import matplotlib.pyplot as plt

x = ["Local", "1us\n100Gbps", "1us\n40Gbps", "1us\n10Gbps",  "5us\n100Gbps", "5us\n40Gbps", "5us\n10Gbps",  "10us\n100Gbps", "10us\n40Gbps", "10us\n10Gbps"]
y = [1430.414718, 1451.291416, 1451.052191, 1490.643886, 1456.001509, 1451.658589, 1478.067304, 1460.382587, 1459.552041, 1498.193247]
x_ticks = np.arange(0, len(y)) + 1


fig = plt.figure(1, figsize=(12,6))
ax = fig.add_subplot(111)
bp = ax.bar(x_ticks, y, 0.5, align='center')
ax.set_xticks(x_ticks)
ax.set_xticklabels(x)
ax.set_ylim([1400,1550])

plt.ylabel("Application Runtime (s)")
plt.title(sys.argv[0])
plt.savefig(sys.argv[0].replace(".py", ".png"))
plt.show()

