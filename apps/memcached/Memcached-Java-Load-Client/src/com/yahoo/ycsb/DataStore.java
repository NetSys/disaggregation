package com.yahoo.ycsb;

import java.util.Properties;


public abstract class DataStore {
	/**
	 * Properties for configuring this DB.
	 */
	Properties _p = new Properties();

	/**
	 * Set the properties for this DB.
	 */
	public void setProperties(Properties p) {
		_p = p;

	}

	/**
	 * Get the set of properties for this DB.
	 */
	public Properties getProperties() {
		return _p;
	}

	/**
	 * Initialize any state for this DB. Called once per DB instance; there is
	 * one DB instance per client thread.
	 */
	public void init() throws DataStoreException {
	}

	/**
	 * Cleanup any state for this DB. Called once per DB instance; there is one
	 * DB instance per client thread.
	 */
	public void cleanup() throws DataStoreException {
	}
}
