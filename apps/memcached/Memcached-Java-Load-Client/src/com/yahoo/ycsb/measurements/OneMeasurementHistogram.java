/**                                                                                                                                                                                
 * Copyright (c) 2010 Yahoo! Inc. All rights reserved.                                                                                                                             
 *                                                                                                                                                                                 
 * Licensed under the Apache License, Version 2.0 (the "License"); you                                                                                                             
 * may not use this file except in compliance with the License. You                                                                                                                
 * may obtain a copy of the License at                                                                                                                                             
 *                                                                                                                                                                                 
 * http://www.apache.org/licenses/LICENSE-2.0                                                                                                                                      
 *                                                                                                                                                                                 
 * Unless required by applicable law or agreed to in writing, software                                                                                                             
 * distributed under the License is distributed on an "AS IS" BASIS,                                                                                                               
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or                                                                                                                 
 * implied. See the License for the specific language governing                                                                                                                    
 * permissions and limitations under the License. See accompanying                                                                                                                 
 * LICENSE file.                                                                                                                                                                   
 */

package com.yahoo.ycsb.measurements;

import java.io.IOException;
import java.util.HashMap;
import java.util.Iterator;

import com.yahoo.ycsb.Config;
import com.yahoo.ycsb.measurements.exporter.MeasurementsExporter;

/**
 * Take measurements and maintain a histogram of a given metric, such as READ
 * LATENCY.
 * 
 * @author cooperb
 *
 */
public class OneMeasurementHistogram extends OneMeasurement {
	private static final long serialVersionUID = 8771477575164658300L;
	
	int[] histogram;
	int histogramoverflow;
	int operations;
	long totallatency;

	int exp_offset;
	double stddev_pts;
	int min;
	int max;
	HashMap<Integer, int[]> returncodes;

	public OneMeasurementHistogram(String name) {
		super(name);
		histogram = new int[Config.getConfig().histogram_buckets];
		histogramoverflow = 0;
		operations = 0;
		totallatency = 0;
		exp_offset = 8;
		stddev_pts = 0;
		min = -1;
		max = -1;
		returncodes = new HashMap<Integer, int[]>();
	}

	/*
	 * (non-Javadoc)
	 * 
	 * @see com.yahoo.ycsb.OneMeasurement#reportReturnCode(int)
	 */
	public synchronized void reportReturnCode(int code) {
		Integer Icode = code;
		if (!returncodes.containsKey(Icode)) {
			int[] val = new int[1];
			val[0] = 0;
			returncodes.put(Icode, val);
		}
		returncodes.get(Icode)[0]++;
	}

	/*
	 * (non-Javadoc)
	 * 
	 * @see com.yahoo.ycsb.OneMeasurement#measure(int)
	 */
	public synchronized void measure(int latency) {
		if (((int)Math.pow(2.0, (double)(Config.getConfig().histogram_buckets - 1)) < latency))
			histogramoverflow++;
		
		for (int i = 0; i < Config.getConfig().histogram_buckets - 1; i++) {
			if (latency < Math.pow(2.0, (double)(i + exp_offset))) {
				histogram[i]++;
				break;
			}
		}
		
		operations++;
		totallatency += latency;
		
		double mean = totallatency / operations;
		stddev_pts += Math.pow((latency - mean), 2.0);

		if ((min < 0) || (latency < min)) {
			min = latency;
		}

		if ((max < 0) || (latency > max)) {
			max = latency;
		}
	}
	
	@Override
	public synchronized void add(OneMeasurement m) {
		operations += histogramoverflow;
		totallatency += ((OneMeasurementHistogram)m).totallatency;
		for (int i = 0; i < Config.getConfig().histogram_buckets; i++) {
			this.histogram[i] += ((OneMeasurementHistogram)m).histogram[i];
			this.operations += ((OneMeasurementHistogram)m).histogram[i];
		}
		
		Iterator<Integer> itr = m.getReturnCodes().keySet().iterator();
		while (itr.hasNext()) {
			Integer item = itr.next();
			if (!this.returncodes.containsKey(item)) {
				this.returncodes.put(item, m.getReturnCodes().get(item));
			} else {
				int[] newcodes = new int[1];
				newcodes[0] = returncodes.get(item)[0] + m.getReturnCodes().get(item)[0];
				returncodes.put(item, newcodes);
			}
		}
	}

	@Override
	public void exportMeasurements(MeasurementsExporter exporter) throws IOException {
		double mean = ((double)totallatency / (double)operations);
		//double stddev = Math.sqrt(stddev_pts/operations);
		exporter.write(getName(), "Operations", operations);
		exporter.write(getName(), "AverageLatency", computeTime(mean));
		//exporter.write(getName(), "Standard Deviation", stddev);
		exporter.write(getName(), "MinLatency", computeTime((double)min));
		exporter.write(getName(), "MaxLatency", computeTime((double)max));
		exporter.write(getName(), "95thPercentileLatency", computeTime((int)getPercentile(histogram, .95)));
		exporter.write(getName(), "99thPercentileLatency", computeTime((int)getPercentile(histogram, .99)));
		exporter.write(getName(), "99.9thPercentileLatency", computeTime((int)getPercentile(histogram, .999)));
		
		for (Integer I : returncodes.keySet()) {
			int[] val = returncodes.get(I);
			exporter.write(getName(), "Return=" + I, val[0]);
		}

		String lower_bound;
		String upper_bound;
		for (int i = 0; i < Config.getConfig().histogram_buckets; i++) {
			if (i == 0)
				lower_bound = computeTime(0);
			else
				lower_bound = computeTime((int)Math.pow(2.0, (double)(i + exp_offset - 1)));
			upper_bound = computeTime((int)Math.pow(2.0, (double)(i + exp_offset)));
			exporter.write(getName(), (lower_bound + " - " + upper_bound), histogram[i]);
			
		}
		String overflowtime = computeTime((int)Math.pow(2.0, (double)((Config.getConfig().histogram_buckets + exp_offset - 1))));
		exporter.write(getName(), ">" + overflowtime, histogramoverflow);
	}
	
	@Override
	public String getSummary() {
		if (operations == 0) {
			return "";
		}
		String avg = computeTime((int)(((double) totallatency) / ((double) operations)));
		String p99 = computeTime((int)getPercentile(histogram, .99));
		
		return "[" + getName() + " total=" + operations + "  avg=" + avg + " 99th=" + p99 + "]";
	}
	
	public double getPercentile(int[] data, double percentile) {
		int i;
		int opcounter = 0;
		for (i = 0; i < Config.getConfig().histogram_buckets; i++) {
			opcounter += data[i];
			if (((double) opcounter) / ((double) operations) >= percentile) {
				break;
			}
		}
		return (Math.pow(2, (i + 1 + exp_offset)));
	}
	
	public long getOperations() { return operations; }
	
	public HashMap<Integer, int[]> getReturnCodes() { return returncodes; }
}
