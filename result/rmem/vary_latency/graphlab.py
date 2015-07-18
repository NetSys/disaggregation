## numpy is used for creating fake data
import numpy as np 
import sys

import matplotlib.pyplot as plt

## Create data
data = [
[1121.811808,	1126.405235,	1128.729621,	1143.597128,	1182.301897],
[1124.250645,	1130.901809,	1134.033044,	1135.896445,	1139.303274],
[1126.806132,	1128.429502,	1132.64236,	1133.82718,	1146.97888],
[1155.038453,	1163.649356,	1167.422184,	1175.896007,	1178.66359],
[1120.135012,	1123.279183,	1127.70737,	1133.511524,	1140.0936],
[1129.464854,	1130.321727,	1132.085308,	1133.649034,	1140.764935],
[1161.334968,	1164.489854,	1168.807983,	1172.347218,	1188.112752]
]

fig = plt.figure(1, figsize=(8,6))
ax = fig.add_subplot(111)
bp = ax.boxplot(data)
ax.set_xticklabels(['Local','1us\n100G','1us\n40G','1us\n10G','10us\n100G','10us\n40G', '10us\n10G'])
plt.ylabel("Application Runtime (s)")
plt.title(sys.argv[0])
plt.savefig(sys.argv[0].replace(".py", ".png"))
plt.show()
