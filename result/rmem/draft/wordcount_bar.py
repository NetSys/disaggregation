## numpy is used for creating fake data
import numpy as np 
import sys

import matplotlib.pyplot as plt

x = ["Local", "1us\n100Gbps", "1us\n40Gbps", "1us\n10Gbps",  "5us\n100Gbps", "5us\n40Gbps", "5us\n10Gbps",  "10us\n100Gbps", "10us\n40Gbps", "10us\n10Gbps"]
y = [300.631011,318.244909,322.6198339,394.2478559,353.5432601,359.1312552,462.792697,429.1272759,410.5162148,480.8412008]
x_ticks = np.arange(0, len(y)) + 1


fig = plt.figure(1, figsize=(12,6))
ax = fig.add_subplot(111)
bp = ax.bar(x_ticks, y, 0.5, align='center')
ax.set_xticks(x_ticks)
ax.set_xticklabels(x)


plt.ylabel("Application Runtime (s)")
plt.title(sys.argv[0])
plt.savefig(sys.argv[0].replace(".py", ".png"))
plt.show()
