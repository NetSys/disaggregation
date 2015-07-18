## numpy is used for creating fake data
import numpy as np 
import sys

import matplotlib.pyplot as plt

## Create data
data = [
[430.9698708,	435.1191405,	442.0508906,	453.7869085,	458.7878051],
[438.1967418,	446.6416286,	453.7420347,	464.899614,	468.69819],
[452.615346,	455.1812701,	462.1486685,	467.8320754,	478.002593],
[542.8719928,	553.5489332,	563.3355734,	568.4769131,	586.0220051],
[439.973505,	449.1673398,	453.2305084,	459.7764015,	467.0658371],
[440.853632,	448.7293558,	454.0287174,	459.2857168,	461.9470451],
[543.516362,	550.7222689,	560.8215476,	569.6400178,	591.9240398]
]


fig = plt.figure(1, figsize=(8,6))
ax = fig.add_subplot(111)
bp = ax.boxplot(data)
ax.set_xticklabels(['Local','1us\n100G','1us\n40G','1us\n10G','10us\n100G','10us\n40G', '10us\n10G'])
plt.ylabel("Application Runtime (s)")
plt.title(sys.argv[0])
plt.savefig(sys.argv[0].replace(".py", ".png"))
plt.show()
