## numpy is used for creating fake data
import numpy as np 
import sys

import matplotlib.pyplot as plt

x = ["Local", "1ns\n100Gbps", "1ns\n40Gbps", "1ns\n10Gbps",  "5ns\n100Gbps", "5ns\n40Gbps", "5ns\n10Gbps",  "10ns\n100Gbps", "10ns\n40Gbps", "10ns\n10Gbps"]
y = [617.893348, 617.4446468, 625.6844411, 656.6117501, 637.6699739, 623.6812029, 660.61659, 645.9626222, 654.695941, 690.7155449]
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
