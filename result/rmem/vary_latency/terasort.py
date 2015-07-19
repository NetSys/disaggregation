## numpy is used for creating fake data
import numpy as np 
import sys

import matplotlib.pyplot as plt

## Create data
data = [
[283.315254,	285.9460764,	289.7629321,	298.2825661,	300.2651532],
[294.3709779,	299.7291399,	305.8255026,	313.4386394,	344.5292611],
[297.2607441,	300.2935336,	307.283007,	315.4085631,	322.284735],
[312.1663661,	326.4860505,	332.3088055,	337.8050607,	340.343168],
[297.6742928,	301.7072152,	306.672482,	315.247388,	321.2286642],
[297.298347,	302.4461067,	314.8420224,	315.4789657,	318.3714681],
[313.4655099,	318.3528698,	324.206617,	330.5687907,	364.424572]
]


fig = plt.figure(1, figsize=(8,6))
ax = fig.add_subplot(111)
bp = ax.boxplot(data)
ax.set_xticklabels(['Local','1us\n100G','1us\n40G','1us\n10G','10us\n100G','10us\n40G', '10us\n10G'])
plt.ylabel("Application Runtime (s)")
plt.title(sys.argv[0])
plt.savefig(sys.argv[0].replace(".py", ".png"))
plt.show()
