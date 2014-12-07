import plotter

queueSizes = [3,4,5,6]

def getDataPoints(filename):
    f = open(filename).readlines()
    data = {x.split()[1]:[float(i) for i in x.split()[2:]] for x in f}
    return [data['2'], data['5'], data['10'], data['20']]

def plot(inputFile, title, outputFile):
    dps = getDataPoints(inputFile)
    plotter.PlotN([queueSizes,queueSizes,queueSizes, queueSizes], dps, 
            YTitle=title, XTitle='Queue Size', 
            labels=['RTO 2x', 'RTO 5x', 'RTO 10x', 'RTO 20x'], 
            xAxis=[min(queueSizes), max(queueSizes)], yAxis=[0, max(max(i) for i in dps)], legendLoc = 'upper right',
            outputFile=outputFile)

print 'Plots for 0.6 Load'

plot('low_bdp_dead_0.6.txt', 'Dead Packet Percentage', "deadPackets_0.6Load")
plot('low_bdp_drops_0.6.txt', 'Drop Packet Percentage', "dropPackets_0.6Load")
plot('low_bdp_allFCT_0.6.txt', 'Average FCT', "avgFCT_all_0.6Load")
plot('low_bdp_largeFCT_0.6.txt', 'Average FCT \n Large Flows', "avgFCT_large_0.6Load")
plot('low_bdp_allSlowdown_0.6.txt', 'Mean Slowdown', "avgSlowdown_all_0.6Load")
plot('low_bdp_largeSlowdown_0.6.txt', 'Mean Slowdown \n Large Flows', "avgSlowdown_large_0.6Load")
#plot('low_bdp_util_0.6.txt', 'Utilization', "Utilization_0.6Load")

print 'Plots for 0.8 Load'

plot('low_bdp_dead_0.8.txt', 'Dead Packet Percentage', "deadPackets_0.8Load")
plot('low_bdp_drops_0.8.txt', 'Dead Packet Percentage', "dropPackets_0.8Load")
plot('low_bdp_allFCT_0.8.txt', 'Average FCT', "avgFCT_all_0.8Load")
plot('low_bdp_largeFCT_0.8.txt', 'Average FCT \n Large Flows', "avgFCT_large_0.8Load")
plot('low_bdp_allSlowdown_0.8.txt', 'Mean Slowdown', "avgSlowdown_all_0.8Load")
plot('low_bdp_largeSlowdown_0.8.txt', 'Mean Slowdown \n Large Flows', "avgSlowdown_large_0.8Load")
#plot('low_bdp_util_0.8.txt', 'Utilization', "Utilization_0.8Load")
