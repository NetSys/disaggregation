package com.yahoo.ycsb.client;

import java.rmi.NotBoundException;
import java.rmi.RemoteException;
import java.rmi.registry.LocateRegistry;
import java.rmi.registry.Registry;
import java.util.HashMap;
import java.util.Iterator;
import java.util.Set;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.yahoo.ycsb.Config;
import com.yahoo.ycsb.client.LoadThread;
import com.yahoo.ycsb.rmi.MasterRMIInterface;
import com.yahoo.ycsb.rmi.SlaveRMIInterface;

public class MasterClient implements MasterRMIInterface {
	private static final Logger LOG = LoggerFactory.getLogger(MasterClient.class);
	public static MasterClient client = null;
	
	LoadThread lt;
	StatusThread st;
	HashMap<String, Registry> rmiClients;
	
	private MasterClient() {
		lt = null;
		st = null;
		rmiClients = new HashMap<String, Registry>();
	}
	
	public static MasterClient getMasterClient() {
		if (client == null)
			client = new MasterClient();
		return client;
	}
	
	public void init() {
		if (Config.getConfig().do_transactions)
			initSlaveRMI();
	}
	
	private void initSlaveRMI() {
		String[] address;
		
		if (Config.getConfig().slave_address != null) {
			address = Config.getConfig().slave_address.split(",");
			for (int i = 0; i < address.length; i++) {
				try {
		            Registry registry = LocateRegistry.getRegistry(address[i]);
		            registry.lookup(SlaveClient.REGISTRY_NAME);
		            if (registry != null)
		            	rmiClients.put(address[i], registry);
		        } catch (RemoteException e) {
		            LOG.error("Could not connect to slave client at " + address[i]);
		        } catch (NotBoundException e) {
		        	LOG.error("Slave Client not bound at " + address[i]);
				}
			}
		}
	}
	
	public void setupSlaves() {
		int res;
		Set<String> keys = rmiClients.keySet();
		Iterator<String> itr = keys.iterator();
		
		for (int i = 1; itr.hasNext(); i++) {
			String key = itr.next();
			try {
				SlaveRMIInterface loadgen = (SlaveRMIInterface) rmiClients.get(key).lookup(SlaveClient.REGISTRY_NAME);
				res = loadgen.setProperties(Config.getConfig());
				if (res != 0)
					System.out.println("Properties sent to Slave were NULL");
			} catch (NotBoundException e) {
				LOG.error("Could not send properties to " + key + " because slave was not bound\nRemoving slave node from setup");
				rmiClients.remove(key);
			}catch (RemoteException e) {
				LOG.error("Could not send properties to " + key + " because slave is not running\nRemoving slave node from setup");
				rmiClients.remove(key);
			}
		}
	}
	
	public void execute() {
		int res;
		Set<String> keys = rmiClients.keySet();
		Iterator<String> itr = keys.iterator();
		
		while (itr.hasNext()) {
			String key = itr.next();
			try {
				SlaveRMIInterface loadgen = (SlaveRMIInterface) rmiClients.get(key).lookup(SlaveClient.REGISTRY_NAME);
				res = loadgen.execute();
				if (res != 0)
					System.out.println("Error executing slave");
			} catch (NotBoundException e) {
				LOG.error("Could not run test with " + key + " because slave was not bound");
			}catch (RemoteException e) {
				LOG.error("Could not run test with " + key + " because slave is not running");
			}
		}
		lt = new LoadThread();
		st = new StatusThread(lt, rmiClients);
		st.start();
		
		try {
			st.join();
		} catch (InterruptedException e) {
			e.printStackTrace();
		}
	}
	
	public void shutdownSlaves() {
		Set<String> keys = rmiClients.keySet();
		Iterator<String> itr = keys.iterator();
		
		while (itr.hasNext()) {
			String key = itr.next();
			try {
				SlaveRMIInterface loadgen = (SlaveRMIInterface) rmiClients.get(key).lookup(SlaveClient.REGISTRY_NAME);
				loadgen.shutdown();
			} catch (NotBoundException e) {
				LOG.error("Could not run test with " + key + " because slave was not bound");
			}catch (RemoteException e) {
				LOG.error("Could not run test with " + key + " because slave is not running");
			}
		}
	}

	@Override
	public void changeWorkingSet(int workingset) throws RemoteException {
		// TODO Auto-generated method stub
		
	}

	@Override
	public void changeThroughput(int throughput) throws RemoteException {
		// TODO Auto-generated method stub
		
	}

	@Override
	public void changeItemCount(int delta, int seconds, int maxitems)
			throws RemoteException {
		// TODO Auto-generated method stub
		
	}
}
