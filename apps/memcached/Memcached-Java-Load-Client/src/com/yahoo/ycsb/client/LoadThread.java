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

package com.yahoo.ycsb.client;

import com.yahoo.ycsb.Config;
import com.yahoo.ycsb.Workload;
import com.yahoo.ycsb.WorkloadException;
import com.yahoo.ycsb.measurements.Measurements;

/**
 * Main class for executing YCSB.
 */
public class LoadThread extends Thread {
	private Workload workload;
	
	public LoadThread() {
		this.workload = null;
		
		if (!Config.getConfig().do_transactions)
			Config.getConfig().operation_count = Config.getConfig().record_count;
		
		ClassLoader classLoader = LoadThread.class.getClassLoader();
		try {
			@SuppressWarnings("rawtypes")
			Class workloadclass = classLoader.loadClass(Config.getConfig().workload);
			workload = (Workload) workloadclass.newInstance();
		} catch (InstantiationException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		} catch (IllegalAccessException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		} catch (ClassNotFoundException e) {
			System.out.println("Workload " + Config.getConfig().workload + " cannot be found");
			System.exit(0);
		}
		
		try {
			workload.init();
		} catch (WorkloadException e) {
			e.printStackTrace();
			System.exit(0);
		}
	}
	
	public void run() {
		// Run the client threads
		Config config = Config.getConfig();
		ClientThreadPool pool = new ClientThreadPool(config.thread_count, config.operation_count, workload);
		pool.join();
		
		// Wait until the status thread grabs the last piece of stats data
		while (Measurements.getMeasurements().getPartialData().size() > 0) {
			try {
				Thread.sleep(500);
			} catch (InterruptedException e) {
				e.printStackTrace();
			}
		}
		// Cleanup the worker threads workspace
		try {
			workload.cleanup();
		} catch (WorkloadException e) {
			e.printStackTrace(System.out);
			System.exit(0);
		}
	}
}
