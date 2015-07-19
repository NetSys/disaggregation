## numpy is used for creating fake data
import numpy as np 
import sys

import matplotlib.pyplot as plt

## Create data
data = [
[145.2808201,	150.2782249,	150.2923535,	150.3015572,	155.3605239],
[150.279978,	150.2865418,	150.2977599,	151.3160322,	155.2971859],
[150.2732172,	150.2814569,	150.291135,	150.3062176,	150.329097],
[150.272711,	150.2791192,	150.283021,	150.2955611,	150.3101802],
[150.2739692,	150.2826136,	150.2892405,	150.3012168,	155.3047891],
[150.2705979,	150.27748,	150.2834388,	150.2929059,	150.2980859],
[150.2749999,	150.2808755,	150.2880379,	150.3120869,	155.2824359]
]

fig = plt.figure(1, figsize=(8,6))
ax = fig.add_subplot(111)
bp = ax.boxplot(data)
ax.set_xticklabels(['Local','1us\n100G','1us\n40G','1us\n10G','10us\n100G','10us\n40G', '10us\n10G'])
plt.ylabel("Application Runtime (s)")
plt.title(sys.argv[0])
plt.savefig(sys.argv[0].replace(".py", ".png"))
plt.show()
