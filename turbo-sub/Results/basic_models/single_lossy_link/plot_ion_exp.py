import sys
import numpy
import plotter


def main():
  drop = ['0.01', '0.05', '0.1', '0.15', '0.3']
  fs = [1, 2, 4, 8, 16, 32]
  Yavg = {}; Y99 = {}; Y999 = {}
  for s in fs:
    Yavg[s] = []
    Y99[s] = []
    Y999[s] = []

  for s in fs:
    for d in drop:
      f1 = open('a_'+str(s)+'_'+d+'.txt').readlines()
      f = [x for x in f1 if 'finished' not in x]
      norm = sorted([float(x.split()[3]) for x in f])
      print d, s, numpy.mean(norm), norm[99*len(norm)/100],\
        norm[999*len(norm)/1000]
      Yavg[s].append(numpy.mean(norm))
      Y99[s].append(norm[99*len(norm)/100])
      Y999[s].append(norm[999*len(norm)/1000])

  Y1 = []; Y2 = []; Y3 = []; X = []
  for s in fs:
    Y1.append(Yavg[s])
    Y2.append(Y99[s])
    Y3.append(Y999[s])
    X.append([float(x) for x in drop])

  lb = [str(s) for s in fs]
  #print Y1
  #print Y2
  #print Y3
  plotter.PlotN(X, Y1, \
    YTitle='Norm FCT (Avg)', XTitle='Drop Probability',
    labels=lb, legendLoc='upper left', legendOff=False,\
    figSize=[7.8, 2.6], onlyLine=False,\
    lWidth=2, mSize=8, legendSize=14,\
    xAxis=[0, 0.3001], yAxis=[1, 4],
    outputFile="FCT_avg_fb_1Gbps")

  plotter.PlotN(X, Y2, \
    YTitle='Norm FCT (99%)', XTitle='Drop Probability',
    labels=lb, legendLoc='upper left', legendOff=False,\
    figSize=[7.8, 2.6], onlyLine=False,\
    lWidth=2, mSize=8, legendSize=14,\
    xAxis=[0, 0.3001], yAxis=[1, 4],
    outputFile="FCT_99_fb_1Gbps")

  plotter.PlotN(X, Y3, \
    YTitle='Norm FCT (99.9%)', XTitle='Drop Probability',
    labels=lb, legendLoc='upper left', legendOff=False,\
    figSize=[7.8, 2.6], onlyLine=False,\
    lWidth=2, mSize=8, legendSize=14,\
    xAxis=[0, 0.3001], yAxis=[1, 6],
    outputFile="FCT_99_9_fb_1Gbps")
  #return large_flow_info

main()
