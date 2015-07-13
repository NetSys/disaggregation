package com.yahoo.ycsb.rmi;

import java.rmi.Remote;
import java.rmi.RemoteException;
import java.util.HashMap;

import com.yahoo.ycsb.Config;
import com.yahoo.ycsb.measurements.OneMeasurement;

public interface SlaveRMIInterface extends Remote {

	public int execute() throws RemoteException;
	
	public Thread.State getStatus() throws RemoteException;
	
	public HashMap<String, OneMeasurement> getCurrentStats() throws RemoteException;
	
	public void shutdown() throws RemoteException;
	
	public int setProperties(Config c) throws RemoteException;
}
