import sys
sys.path.insert(0, '../..')
import numpy
import plotter
import random
import parse_ns2_trace as parse
import ideal as ideal


def plot_cdf(fct, fct_large, 
             output):
  Y1 = [1.0 * i / len(fct) for i in range(len(fct))]
  Y2 = [1.0 * i / len(fct_large) for i in range(len(fct_large))]
  X1 = sorted(fct)
  X2 = sorted(fct_large)
  #X3 = sorted(ideal_fct)
  #X4 = sorted(ideal_fct_large)
  plotter.PlotN([X1, X2], \
    [Y1, Y2], \
    YTitle='CDF', XTitle='Normalized FCT', \
    labels=['All', '>10MB'], \
    legendLoc='lower right', legendOff=False,\
    figSize=[7.8, 2.6], onlyLine=True,\
    lWidth=2, mSize=8, legendSize=18,\
    xAxis=[0, max(max(X1), max(X2))], yAxis=[0, 1],
    outputFile=output)

def plot_norm_binned(flow_info, ideal_fct, output):
  max_size = max([x[0] for x in flow_info])
  # split in 100KB chunks
  bin_size = 100000
  num_bins = 1 + int(max_size / bin_size)
  norm_fct_binned = [[] for i in range(num_bins)]
  norm_fct_ideal_binned = [[] for i in range(num_bins)]
  for i in range(len(flow_info)):
    f = flow_info[i]
    bin = int(f[0] / bin_size)
    norm_fct_binned[bin].append(f[3])
    norm_fct_ideal_binned[bin].append(ideal_fct[i] / f[2])
  avg_norm_fct_binned = [numpy.mean(x) for x in norm_fct_binned]
  avg_norm_fct_ideal_binned = [numpy.mean(x) for x in norm_fct_ideal_binned]
  x = range(num_bins)
  plotter.PlotN([x, x], [avg_norm_fct_binned, avg_norm_fct_ideal_binned], \
    YTitle='Avg. Norm FCT', XTitle='Bin (100KB)', \
    labels=['pFabric', 'Ideal'], legendLoc='upper left', legendOff=False,\
    figSize=[7.8, 2.6], onlyLine=True,\
    lWidth=2, mSize=8, legendSize=18,\
    xAxis=[0, num_bins], yAxis=[0, max(avg_norm_fct_binned)],
    outputFile=output)


def plot_norm_timed(flow_info, ideal_fct, output):
  # split in 100 chunks
  num_bins = 100
  bin_size = len(flow_info) / num_bins
  norm_fct_binned = [[] for i in range(num_bins)]
  for i in range(len(flow_info)):
    f = flow_info[i]
    bin = int(i / bin_size)
    norm_fct_binned[bin].append(f[3])
  avg_norm_fct_binned = [numpy.mean(x) for x in norm_fct_binned]
  x = range(num_bins)
  plotter.PlotN([x], [avg_norm_fct_binned], \
    YTitle='Avg. Norm FCT', XTitle='Bin (' + str(bin_size) + ' flows)', \
    labels=['All', '>10MB'], legendLoc='lower right', legendOff=True,\
    figSize=[7.8, 2.6], onlyLine=True,\
    lWidth=2, mSize=8, legendSize=18,\
    xAxis=[0, num_bins], yAxis=[0, max(avg_norm_fct_binned)],
    outputFile=output)


def plot_size_timed(flow_info, ideal_fct, output):
  # split in 100 chunks
  num_bins = 100
  bin_size = len(flow_info) / num_bins
  size_timed = [[] for i in range(num_bins)]
  for i in range(len(flow_info)):
    f = flow_info[i]
    bin = int(i / bin_size)
    size_timed[bin].append(f[0] / 1000000.0)
  avg_size_timed = [numpy.mean(x) for x in size_timed]
  #print avg_size_timed
  max_size_timed = [max(x) for x in size_timed]
  #print avg_size_timed
  x = range(num_bins)
  plotter.PlotN([x, x], [avg_size_timed, max_size_timed], \
    YTitle='Size (MB)', XTitle='Bin (' + str(bin_size) + ' flows)', \
    labels=['Avg.', 'Max'], legendLoc='center right', legendOff=False,\
    figSize=[7.8, 2.6], onlyLine=True,\
    lWidth=2, mSize=8, legendSize=18,\
    xAxis=[0, num_bins], yAxis=[0, 35],
    outputFile=output)

def SylviaPlot(Y, X1, X2, labels=None, XTitle='X', YTitle='Y',
          xAxis=None, yAxis=None,
          onlyLine=False,
          mSize=6, lWidth=1,
          legendLoc='upper left', legendSize=18, legendTitle=None,
          isLegendOutside=False, bboxPos=None, legendOff=False,
          gridOff=False, xTicks=None, yTicks=None,
          outputFile='figure', ext='pdf', fccolor='white', isDark=False, figSize=[8.5, 3]):

    if xAxis == None or yAxis == None or labels == None:
        print "Please specify axis limits and labels"
        return
    fig = plotter.Figure(figSize)
    ax1 = fig.add_subplot()
    if isDark:
      params = { 'axes.labelcolor': 'white'}
      plt.rcParams.update(params)
    #for i in range(len(Y)):
    ax1.hlines(Y, X1, X2,
              linewidth=lWidth, colors=[plotter.colors[0]],
              clip_on=False)
    #ax1.set_yscale('log')
    lgd = plotter.SetupFig(fig, ax1, xAxis, yAxis, XTitle, YTitle,
             isLegendOutside, legendLoc, legendTitle, legendSize, bboxPos, legendOff,
             gridOff, xTicks, yTicks,
             outputFile, ext, fccolor)
    fig.plt.savefig(outputFile + "." + ext, facecolor=fccolor, format=ext, \
      bbox_inches='tight', dpi=400)


def main():
  loads = ['0.8Load_large']
  for load in loads:
    f = open('Dataset/flow_' + load + '.tr').readlines()
    flow_info = parse.get_flow_info_new(f, 2.5) #Dictionary with indices as keys
    start_times = [float(x.split()[0]) for x in f]
    finish_times = [float(x.split()[1]) for x in f]
    rates = [flow_info[i][0] * 8 / (1000.0 * flow_info[i][1]) for i in range(len(flow_info))]

    sampled_indices = random.sample(range(len(flow_info)), 20000)

    sampled_rates = [rates[i] for i in sampled_indices]
    sampled_start_times = [start_times[i] for i in sampled_indices]
    sampled_finish_times = [finish_times[i] for i in sampled_indices]


    print min(rates), max(rates)
    SylviaPlot(sampled_rates, sampled_start_times, sampled_finish_times, \
      labels=[''], XTitle='Time', YTitle='Throughput (10 Gbps)', xAxis=[1.0, 13], yAxis=[0, 10], \
      outputFile='SylviaPlot')

main()
