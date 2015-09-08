## numpy is used for creating fake data
import numpy as np 
import sys

import matplotlib.pyplot as plt

x = ["Local", "1us\n100Gbps", "1us\n40Gbps", "1us\n10Gbps",  "5us\n100Gbps", "5us\n40Gbps", "5us\n10Gbps",  "10us\n100Gbps", "10us\n40Gbps", "10us\n10Gbps"]
y_data = '''
481.258
491.612
490.928
546.264
529.2
532.782
594.376
600.842
592.848
654.636
'''
print y_data.split("\n")
y = map(float, filter(lambda x: x != '', y_data.split("\n")) )
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
