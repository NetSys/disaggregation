package com.yahoo.ycsb.client;

import java.io.FileOutputStream;
import java.io.IOException;
import java.io.OutputStream;
import java.rmi.NotBoundException;
import java.rmi.RemoteException;
import java.rmi.registry.Registry;
import java.util.HashMap;
import java.util.Iterator;
import java.util.Set;

import com.yahoo.ycsb.Config;
import com.yahoo.ycsb.measurements.Measurements;
import com.yahoo.ycsb.measurements.OneMeasurement;
import com.yahoo.ycsb.measurements.exporter.MeasurementsExporter;
import com.yahoo.ycsb.measurements.exporter.TextMeasurementsExporter;
import com.yahoo.ycsb.rmi.SlaveRMIInterface;

/**
 * A thread to periodically show the status of the experiment, to reassure you
 * that progress is being made.
 * 
 * @author cooperb
 * 
 */
public class StatusThread extends Thread {
	HashMap<String, Registry> rmiClients;
	LoadThread lt;
	String _label;
	boolean _standardstatus;
	long _printstatsinterval;

	public StatusThread(LoadThread lt, HashMap<String, Registry> rmiClients) {
		this.rmiClients = rmiClients;
		this.lt = lt;
		_label = Config.getConfig().label;
		_printstatsinterval = 5;
	}

	/**
	 * Run and periodically report status.
	 */
	public void run() {
		long st = System.currentTimeMillis();
		long en = System.currentTimeMillis();
		boolean alldone;
		lt.start();

		do {
			alldone = true;
			
			if (rmiClients != null) {
				Set<String> keys = rmiClients.keySet();
				Iterator<String> itr = keys.iterator();
				
				while (itr.hasNext()) {
					HashMap<String, OneMeasurement> res = null;
					String key = itr.next();
					try {
						SlaveRMIInterface loadgen = (SlaveRMIInterface) rmiClients.get(key).lookup(SlaveClient.REGISTRY_NAME);
						if (loadgen.getStatus() != Thread.State.TERMINATED) {
							res = loadgen.getCurrentStats();
							if (res != null && !res.isEmpty())
								Measurements.getMeasurements().add(res);
							alldone = false;
						}
					} catch (NotBoundException e) {
						System.out.println("Could not get stats from " + key + " because slave was not bound");
					}catch (RemoteException e) {
						System.out.println("Could not get stats from " + key + " because slave is not running");
					}
	
				}
			}

			// terminate this thread when all the load thread is done
			if (lt.getState() != Thread.State.TERMINATED)
				alldone = false;

			
			if (!alldone) {
				en = System.currentTimeMillis();
				System.out.println(_label + " " + ((en - st) / 1000) + " sec: " 
						+ Measurements.getMeasurements().getSummary() + "\n");
			}

			try {
				sleep(_printstatsinterval * 1000);
			} catch (InterruptedException e) {}

		} while (!alldone);
		
		try {
			exportMeasurements(en - st);
		} catch (IOException e) {
			System.err.println("Could not export measurements, error: "+ e.getMessage());
			e.printStackTrace();
			System.exit(-1);
		}

		try {
			lt.join();
		} catch (InterruptedException e) {
		}
	}
	
	/**
	 * Exports the measurements to either sysout or a file using the exporter
	 * loaded from conf.
	 * 
	 * @throws IOException
	 *             Either failed to write to output stream or failed to close
	 *             it.
	 */
	private void exportMeasurements(long runtime) throws IOException {
		MeasurementsExporter exporter = null;
		try {
			// if no destination file is provided the results will be written to stdout
			OutputStream out;
			String exportFile = Config.getConfig().export_file;
			long opcount = Measurements.getMeasurements().getOperations();
			if (exportFile == null) {
				out = System.out;
			} else {
				out = new FileOutputStream(exportFile);
			}

			// if no exporter is provided the default text one will be used
			String exporterStr = Config.getConfig().exporter;
			try {
				exporter = (MeasurementsExporter) Class.forName(exporterStr).getConstructor(OutputStream.class).newInstance(out);
			} catch (Exception e) {
				System.err.println("Could not find exporter " + exporterStr + ", will use default text reporter.");
				e.printStackTrace();
				exporter = new TextMeasurementsExporter(out);
			}

			exporter.write("OVERALL", "RunTime(ms)", runtime);
			double throughput = 1000.0 * ((double) opcount) / ((double) runtime);
			exporter.write("OVERALL", "Throughput(ops/sec)", throughput);
			
			Measurements.getMeasurements().exportMeasurements(exporter);
		} finally {
			if (exporter != null) {
				exporter.close();
			}
		}
	}
}