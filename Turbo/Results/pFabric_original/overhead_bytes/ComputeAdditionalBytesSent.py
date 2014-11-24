import plotter

fBase = open("Dataset/Re_Base/qston.tr").readlines()[1:-1]
bArrivalsBase = [float(x.split()[0]) for x in fBase]
bDeparturesBase = [float(x.split()[1]) for x in fBase]

overheads = []
overheadDeps = []
delays = [0.001, 0.1, 0.2, 0.4, 0.8, 1.6, 3.2]
for delay in delays:
  f1 = open("Dataset/Re_"+str(delay)+"/qston.tr").readlines()[1:-1]
  flow = open("Dataset/Re_"+str(delay)+"/flow.tr").readlines()
  bArrivals = [float(x.split()[0]) for x in f1]
  bDepartures = [float(x.split()[1]) for x in f1]
  bDrops = [float(x.split()[2]) for x in f1]
  bytes = [bArrivals[i] - bArrivalsBase[i] for i in range(len(f1))]
  bytesDep = [bDepartures[i] - bDeparturesBase[i] for i in range(len(f1))]
  drops = sum(bDrops)
  fSize = [1460 * float(x.split()[0]) for x in flow] 
  sent = sum(bytes)
  sentDep = sum(bytesDep)
  shouldSend = sum(fSize)
  overhead = 100.0 * (1.0 * sent - shouldSend) / shouldSend;
  overheadDep = 100.0 * (1.0 * sentDep - shouldSend) / shouldSend;
  print delay, sent, sentDep, drops, shouldSend, overhead, overheadDep
  overheads.append(overhead)
  overheadDeps.append(overheadDep)
  
plotter.PlotN([delays, delays], [overheads, overheadDeps], \
    YTitle='%Overhead (bytes)', XTitle='Host Delay (us)', \
    labels=['Total', 'In Network'], legendLoc='lower right', legendOff=False,\
    figSize=[7.8, 2.6], onlyLine=False,\
    lWidth=2, mSize=8, legendSize=18,\
    xAxis=[0, 3.5], yAxis=[0, 20],
    outputFile="OverheadPFabric")

