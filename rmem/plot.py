import numpy as np
import matplotlib.pyplot as plt

def get_color(c):
  if c > 0:
    return "blue"
  else:
    return "red"

data = np.loadtxt("rmem_log.txt")
plt.scatter(abs(data[:,1]), data[:,2],color=map(get_color, data[:,1]),marker=".")
plt.xlabel("Time (10s)")
plt.ylabel("Page Addr")
plt.show()