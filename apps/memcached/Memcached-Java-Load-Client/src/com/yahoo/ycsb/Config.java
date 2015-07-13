package com.yahoo.ycsb;

import java.io.Serializable;

public class Config implements Serializable{
	private static final long serialVersionUID = -8722584434179067291L;
	private static Config config = null;
	
	public static final String CHURN_DELTA_PROPERTY = "churndelta";
	public static final String DB_PROPERTY = "db";
	public static final String DO_TRANSACTIONS_PROPERTY = "dotransactions";
	public static final String EXPORTER_PROPERTY = "exporter";
	public static final String EXPORT_FILE_PROPERTY = "exportfile";
	public static final String FIELD_COUNT_PROPERTY = "fieldcount";
	public static final String FIELD_LENGTH_PROPERTY = "fieldlength";
	public static final String HISTOGRAM_BUCKET_PROPERTY = "histogram.buckets";
	public static final String INSERT_ORDER_PROPERTY = "insertorder";
	public static final String INSERT_PROPORTION_PROPERTY = "insertproportion";
	public static final String INSERT_START_PROPERTY = "insertstart";
	public static final String KEY_PREFIX_PROPERTY = "keyprefix";
	public static final String LABEL_PROPERTY = "label";
	public static final String MAX_SCAN_LENGTH_PROPERTY = "maxscanlength";
	public static final String MEASUREMENT_TYPE_PROPERTY = "measurementtype";
	public static final String MEMCACHED_ADDRESS_PROPERTY = "memcached.address";
	public static final String MEMCACHED_PORT_PROPERTY = "memcached.port";
	public static final String MEMADD_PROPORTION_PROPERTY = "memaddproportion";
	public static final String MEMAPPEND_PROPORTION_PROPERTY = "memappendproportion";
	public static final String MEMCAS_PROPORTION_PROPERTY = "memcasproportion";
	public static final String MEMDECR_PROPORTION_PROPERTY = "memdecrproportion";
	public static final String MEMDELETE_PROPORTION_PROPERTY = "memdeleteproportion";
	public static final String MEMGET_PROPORTION_PROPERTY = "memgetproportion";
	public static final String MEMGETS_PROPORTION_PROPERTY = "memgetsproportion";
	public static final String MEMINCR_PROPORTION_PROPERTY = "memincrproporiton";
	public static final String MEMPREPEND_PROPORTION_PROPERTY = "memprependproportion";
	public static final String MEMREPLACE_PROPORTION_PROPERTY = "memreplaceproportion";
	public static final String MEMSET_PROPORTION_PROPERTY = "memsetproportion";
	public static final String MEMUPDATE_PROPORTION_PROPERTY = "memupdateproportion";
	public static final String OPERATION_COUNT_PROPERTY = "operationcount";
	public static final String PRINT_STATS_INTERVAL_PROPERTY = "printstatsinterval";
	public static final String READ_ALL_FIELDS_PROPERTY = "readallfields";
	public static final String READ_PROPORTION_PROPERTY = "readproportion";
	public static final String READMODIFYWRITE_PROPORTION_PROPERTY = "readmodifywriteproportion";
	public static final String RECORD_COUNT_PROPERTY = "recordcount";
	public static final String REQUEST_DISTRIBUTION_PROPERTY = "requestdistribution";
	public static final String SCAN_LENGTH_DISTRIBUTION_PROPERTY = "scanlengthdistribution";
	public static final String SCAN_PROPORTION_PROPERTY = "scanproportion";
	public static final String SLAVE_ADDRESS_PROPERTY = "slaveaddress";
	public static final String TABLENAME_PROPERTY = "table";
	public static final String TARGET_PROPERTY = "target";
	public static final String THREAD_COUNT_PROPERTY = "threadcount";
	public static final String TIMESERIES_GRANULARITY_PROPERTY = "timeseries.granularity";
	public static final String UPDATE_PROPORTION_PROPERTY = "updateproportion";
	public static final String VALUE_LENGTH_PROPERTY = "valuelength";
	public static final String WORKING_SET_PROPERTY = "workingset";
	public static final String WORKLOAD_PROPERTY = "workload";
	public static final String WRITE_ALL_FIELDS_PROPERTY = "writeallfields";
	
	public int churn_delta = 1;
	public String db = null;
	public boolean do_transactions = false;
	public String exporter = "com.yahoo.ycsb.measurements.exporter.TextMeasurementsExporter";
	public String export_file = null;
	public int field_count = 10;
	public int field_length = 100;
	public int histogram_buckets = 20;
	public String insert_order = "hashed";
	public double insert_proportion = 0.0;
	public int insert_start = 0;
	public String key_prefix = "user";
	public int operation_count = 0;
	public String label = "";
	public int max_scan_length = 1000;
	public String measurement_type = "histogram";
	public String memcached_address = null;
	public int memcached_port = 11211;
	public double memadd_proportion = 0.0;
	public double memappend_proportion = 0.0;
	public double memcas_proportion = 0.0;
	public double memdecr_proportion = 0.0;
	public double memdelete_proportion = 0.0;
	public double memget_proportion = 0.95;
	public double memgets_proportion = 0.0;
	public double memincr_proportion = 0.0;
	public double memprepend_proportion = 0.0;
	public double memreplace_proportion = 0.0;
	public double memset_proportion = 0.0;
	public double memupdate_proportion = 0.05;
	public int print_stats_interval = 5;
	public boolean read_all_fields = true;
	public double read_proportion = 0.95;
	public double read_write_modify_proportion = 0.0;
	public int record_count = 0;
	public String request_distribution = "zipfian";
	public String scan_length_distribution = "uniform";
	public double scan_proportion = 0.0;
	public String slave_address = null;
	public String table_name = "usertable";
	public int target = 0;
	public int thread_count = 1;
	public int timeseries_granularity = 1000;
	public double update_proportion = 0.05;
	public int working_set = 1;
	public int value_length = 256;
	public String workload = null;
	public boolean write_all_fields = false;
	
	public static final String INSERT_COUNT_PROPERTY = "insertcount";
	
	private Config() {
	}
	
	public static Config getConfig() {
		if (config == null)
			return (config = new Config());
		return config;
	}
	
	public void setProperty(String property, String value) {
		try {
			if (property.equals(CHURN_DELTA_PROPERTY)) {
				churn_delta = (new Integer(value)).intValue();
			} else if (property.equals(DB_PROPERTY)) {
				db = value;
			} else if (property.equals(DO_TRANSACTIONS_PROPERTY)) {
				do_transactions = (new Boolean(value)).booleanValue();
			} else if (property.equals(EXPORTER_PROPERTY)) {
				exporter = value;
			} else if (property.equals(EXPORT_FILE_PROPERTY)) {
				export_file = value;
			} else if (property.equals(FIELD_COUNT_PROPERTY)) {
				field_count = (new Integer(value)).intValue();
			} else if (property.equals(FIELD_LENGTH_PROPERTY)) {
				field_length = (new Integer(value)).intValue();
			} else if (property.equals(HISTOGRAM_BUCKET_PROPERTY)) {
				histogram_buckets = (new Integer(value)).intValue();
			} else if (property.equals(INSERT_ORDER_PROPERTY)) {
				insert_order = value;
			} else if (property.equals(INSERT_PROPORTION_PROPERTY)) {
				insert_proportion = (new Double(value)).doubleValue();
			} else if (property.equals(INSERT_START_PROPERTY)) {
				insert_start = (new Integer(value)).intValue();
			} else if (property.equals(KEY_PREFIX_PROPERTY)) {
				key_prefix = value;
			} else if (property.equals(LABEL_PROPERTY)) {
				label = value;
			} else if (property.equals(MAX_SCAN_LENGTH_PROPERTY)) {
				max_scan_length = (new Integer(value)).intValue();
			} else if (property.equals(MEASUREMENT_TYPE_PROPERTY)) {
				measurement_type = value;
			} else if (property.equals(MEMCACHED_ADDRESS_PROPERTY)) {
				memcached_address = value;
			} else if (property.equals(MEMCACHED_PORT_PROPERTY)) {
				memcached_port = (new Integer(value)).intValue();
			} else if (property.equals(MEMADD_PROPORTION_PROPERTY)) {
				memadd_proportion = (new Double(value)).doubleValue();
			} else if (property.equals(MEMAPPEND_PROPORTION_PROPERTY)) {
				memappend_proportion = (new Double(value)).doubleValue();
			} else if (property.equals(MEMCAS_PROPORTION_PROPERTY)) {
				memcas_proportion = (new Double(value)).doubleValue();
			} else if (property.equals(MEMDECR_PROPORTION_PROPERTY)) {
				memdecr_proportion = (new Double(value)).doubleValue();
			} else if (property.equals(MEMDELETE_PROPORTION_PROPERTY)) {
				memdelete_proportion = (new Double(value)).doubleValue();
			} else if (property.equals(MEMGET_PROPORTION_PROPERTY)) {
				memget_proportion = (new Double(value)).doubleValue();
			} else if (property.equals(MEMGETS_PROPORTION_PROPERTY)) {
				memgets_proportion = (new Double(value)).doubleValue();
			} else if (property.equals(MEMINCR_PROPORTION_PROPERTY)) {
				memincr_proportion = (new Double(value)).doubleValue();
			} else if (property.equals(MEMPREPEND_PROPORTION_PROPERTY)) {
				memprepend_proportion = (new Double(value)).doubleValue();
			} else if (property.equals(MEMREPLACE_PROPORTION_PROPERTY)) {
				memreplace_proportion = (new Double(value)).doubleValue();
			} else if (property.equals(MEMSET_PROPORTION_PROPERTY)) {
				memset_proportion = (new Double(value)).doubleValue();
			} else if (property.equals(MEMUPDATE_PROPORTION_PROPERTY)) {
				memupdate_proportion = (new Double(value)).doubleValue();
			} else if (property.equals(OPERATION_COUNT_PROPERTY)) {
				operation_count = (new Integer(value)).intValue();
			} else if (property.equals(PRINT_STATS_INTERVAL_PROPERTY)) {
				print_stats_interval = (new Integer(value)).intValue();
			} else if (property.equals(READ_ALL_FIELDS_PROPERTY)) {
				read_all_fields = (new Boolean(value)).booleanValue();
			} else if (property.equals(READ_PROPORTION_PROPERTY)) {
				read_proportion = (new Double(value)).doubleValue();
			} else if (property.equals(READMODIFYWRITE_PROPORTION_PROPERTY)) {
				read_write_modify_proportion = (new Double(value)).doubleValue();
			} else if (property.equals(RECORD_COUNT_PROPERTY)) {
				record_count = (new Integer(value)).intValue();
			} else if (property.equals(REQUEST_DISTRIBUTION_PROPERTY)) {
				request_distribution = value;
			} else if (property.equals(SCAN_LENGTH_DISTRIBUTION_PROPERTY)) {
				scan_length_distribution = value;
			} else if (property.equals(SCAN_PROPORTION_PROPERTY)) {
				scan_proportion = (new Double(value)).doubleValue();
			} else if (property.equals(SLAVE_ADDRESS_PROPERTY)) {
				slave_address = value;
			} else if (property.equals(TABLENAME_PROPERTY)) {
				table_name = value;
			} else if (property.equals(TARGET_PROPERTY)) {
				target = (new Integer(value)).intValue();
			} else if (property.equals(THREAD_COUNT_PROPERTY)) {
				thread_count = (new Integer(value)).intValue();
			} else if (property.equals(TIMESERIES_GRANULARITY_PROPERTY)) {
				timeseries_granularity = (new Integer(value)).intValue();
			} else if (property.equals(UPDATE_PROPORTION_PROPERTY)) {
				update_proportion = (new Double(value)).doubleValue();
			} else if (property.equals(VALUE_LENGTH_PROPERTY)) {
				value_length = (new Integer(value)).intValue();
			} else if (property.equals(WORKING_SET_PROPERTY)) {
				working_set = (new Integer(value)).intValue();
			} else if (property.equals(WORKLOAD_PROPERTY)) {
				workload = value;
			} else if (property.equals(WRITE_ALL_FIELDS_PROPERTY)) {
				write_all_fields = (new Boolean(value)).booleanValue();
			} else {
				System.out.println("Unknown property " + property + " with value " + value);
				System.exit(0);
			}
		} catch (NumberFormatException e) {
			System.out.println("Error: Property " + property + " has wrong type");
			System.exit(0);
		}
	}
	
	public static void setConfig(Config c) {
		config = c;
	}
}
