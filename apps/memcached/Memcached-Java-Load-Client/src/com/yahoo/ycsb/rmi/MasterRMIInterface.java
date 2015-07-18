package com.yahoo.ycsb.rmi;

import java.rmi.Remote;
import java.rmi.RemoteException;

public interface MasterRMIInterface extends Remote {
	
	public void changeWorkingSet(int workingset) throws RemoteException;
	
	public void changeThroughput(int throughput) throws RemoteException;
	
	public void changeItemCount(int delta, int seconds, int maxitems) throws RemoteException;
}
