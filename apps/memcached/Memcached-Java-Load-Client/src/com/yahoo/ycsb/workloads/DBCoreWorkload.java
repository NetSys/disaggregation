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

package com.yahoo.ycsb.workloads;

import com.yahoo.ycsb.*;
import com.yahoo.ycsb.database.DB;
import com.yahoo.ycsb.generator.ChurnGenerator;
import com.yahoo.ycsb.generator.CounterGenerator;
import com.yahoo.ycsb.generator.DiscreteGenerator;
import com.yahoo.ycsb.generator.Generator;
import com.yahoo.ycsb.generator.IntegerGenerator;
import com.yahoo.ycsb.generator.ScrambledZipfianGenerator;
import com.yahoo.ycsb.generator.SkewedLatestGenerator;
import com.yahoo.ycsb.generator.UniformIntegerGenerator;
import com.yahoo.ycsb.generator.ZipfianGenerator;
import com.yahoo.ycsb.measurements.Measurements;

import java.util.HashMap;
import java.util.HashSet;
import java.util.Vector;

/**
 * The core benchmark scenario. Represents a set of clients doing simple CRUD
 * operations. The relative proportion of different kinds of operations, and
 * other properties of the workload, are controlled by parameters specified at
 * runtime.
 * 
 * Properties to control the client:
 * <UL>
 * <LI><b>fieldcount</b>: the number of fields in a record (default: 10)
 * <LI><b>fieldlength</b>: the size of each field (default: 100)
 * <LI><b>readallfields</b>: should reads read all fields (true) or just one
 * (false) (default: true)
 * <LI><b>writeallfields</b>: should updates and read/modify/writes update all
 * fields (true) or just one (false) (default: false)
 * <LI><b>readproportion</b>: what proportion of operations should be reads
 * (default: 0.95)
 * <LI><b>updateproportion</b>: what proportion of operations should be updates
 * (default: 0.05)
 * <LI><b>insertproportion</b>: what proportion of operations should be inserts
 * (default: 0)
 * <LI><b>scanproportion</b>: what proportion of operations should be scans
 * (default: 0)
 * <LI><b>readmodifywriteproportion</b>: what proportion of operations should be
 * read a record, modify it, write it back (default: 0)
 * <LI><b>requestdistribution</b>: what distribution should be used to select
 * the records to operate on - uniform, zipfian or latest (default: uniform)
 * <LI><b>maxscanlength</b>: for scans, what is the maximum number of records to
 * scan (default: 1000)
 * <LI><b>scanlengthdistribution</b>: for scans, what distribution should be
 * used to choose the number of records to scan, for each scan, between 1 and
 * maxscanlength (default: uniform)
 * <LI><b>insertorder</b>: should records be inserted in order by key
 * ("ordered"), or in hashed order ("hashed") (default: hashed)
 * </ul>
 */
public class DBCoreWorkload extends Workload {

	IntegerGenerator keysequence;

	DiscreteGenerator operationchooser;

	IntegerGenerator keychooser;

	Generator fieldchooser;

	CounterGenerator transactioninsertkeysequence;

	IntegerGenerator scanlength;

	boolean orderedinserts;

	/**
	 * Initialize the scenario. Called once, in the main client thread, before
	 * any operations are started.
	 */
	public void init() throws WorkloadException {
		int recordcount = Config.getConfig().record_count;

		int insertstart = Config.getConfig().insert_start;


		if (Config.getConfig().insert_order.compareTo("hashed") == 0) {
			orderedinserts = false;
		} else {
			orderedinserts = true;
		}

		keysequence = new CounterGenerator(insertstart);
		operationchooser = new DiscreteGenerator();
		if (Config.getConfig().read_proportion > 0) {
			operationchooser.addValue(Config.getConfig().read_proportion, "READ");
		}

		if (Config.getConfig().update_proportion > 0) {
			operationchooser.addValue(Config.getConfig().update_proportion, "UPDATE");
		}

		if (Config.getConfig().insert_proportion > 0) {
			operationchooser.addValue(Config.getConfig().insert_proportion, "INSERT");
		}

		if (Config.getConfig().scan_proportion > 0) {
			operationchooser.addValue(Config.getConfig().scan_proportion, "SCAN");
		}

		if (Config.getConfig().read_write_modify_proportion > 0) {
			operationchooser.addValue(Config.getConfig().read_write_modify_proportion, "READMODIFYWRITE");
		}

		transactioninsertkeysequence = new CounterGenerator(recordcount);
		if (Config.getConfig().request_distribution.compareTo("uniform") == 0) {
			keychooser = new UniformIntegerGenerator(0, recordcount - 1);
		} else if (Config.getConfig().request_distribution.compareTo("zipfian") == 0) {
			// it does this by generating a random "next key" in part by taking
			// the modulus over the number of keys
			// if the number of keys changes, this would shift the modulus, and
			// we don't want that to change which keys are popular
			// so we'll actually construct the scrambled zipfian generator with
			// a keyspace that is larger than exists at the beginning
			// of the test. that is, we'll predict the number of inserts, and
			// tell the scrambled zipfian generator the number of existing keys
			// plus the number of predicted keys as the total keyspace. then, if
			// the generator picks a key that hasn't been inserted yet, will
			// just ignore it and pick another key. this way, the size of the
			// keyspace doesn't change from the perspective of the scrambled
			// zipfian generator

			int opcount = Config.getConfig().operation_count;
			int expectednewkeys = (int) (((double) opcount) * Config.getConfig().insert_proportion * 2.0); // 2
																						// is
																						// fudge
																						// factor

			keychooser = new ScrambledZipfianGenerator(recordcount
					+ expectednewkeys);
		} else if (Config.getConfig().request_distribution.compareTo("latest") == 0) {
			keychooser = new SkewedLatestGenerator(transactioninsertkeysequence);
		}  else if (Config.getConfig().request_distribution.compareTo("churn") == 0){
			keychooser = new ChurnGenerator(Config.getConfig().working_set, Config.getConfig().churn_delta, recordcount);
		} else {
			throw new WorkloadException("Unknown distribution \"" + Config.getConfig().request_distribution + "\"");
		}

		fieldchooser = new UniformIntegerGenerator(0, Config.getConfig().field_count - 1);

		if (Config.getConfig().scan_length_distribution.compareTo("uniform") == 0) {
			scanlength = new UniformIntegerGenerator(1, Config.getConfig().max_scan_length);
		} else if (Config.getConfig().scan_length_distribution.compareTo("zipfian") == 0) {
			scanlength = new ZipfianGenerator(1, Config.getConfig().max_scan_length);
		} else {
			throw new WorkloadException("Distribution \"" + Config.getConfig().scan_length_distribution
					+ "\" not allowed for scan length");
		}
	}

	/**
	 * Do one insert operation. Because it will be called concurrently from
	 * multiple client threads, this function must be thread safe. However,
	 * avoid synchronized, or the threads will block waiting for each other, and
	 * it will be difficult to reach the target throughput. Ideally, this
	 * function would have no side effects other than DB operations.
	 */
	public boolean doInsert(DataStore db) {
		int keynum = keysequence.nextInt();
		if (!orderedinserts) {
			keynum = Utils.hash(keynum);
		}
		String dbkey = "user" + keynum;
		HashMap<String, String> values = new HashMap<String, String>();
		for (int i = 0; i < Config.getConfig().field_count; i++) {
			String fieldkey = "field" + i;
			String data = Utils.ASCIIString(Config.getConfig().field_length);
			values.put(fieldkey, data);
		}
		if (((DB)db).insert(Config.getConfig().table_name, dbkey, values) == 0)
			return true;
		else
			return false;
	}

	/**
	 * Do one transaction operation. Because it will be called concurrently from
	 * multiple client threads, this function must be thread safe. However,
	 * avoid synchronized, or the threads will block waiting for each other, and
	 * it will be difficult to reach the target throughput. Ideally, this
	 * function would have no side effects other than DB operations.
	 */
	public boolean doTransaction(DataStore db) {
		String op = operationchooser.nextString();

		if (op.compareTo("READ") == 0) {
			doTransactionRead((DB)db);
		} else if (op.compareTo("UPDATE") == 0) {
			doTransactionUpdate((DB)db);
		} else if (op.compareTo("INSERT") == 0) {
			doTransactionInsert((DB)db);
		} else if (op.compareTo("SCAN") == 0) {
			doTransactionScan((DB)db);
		} else {
			doTransactionReadModifyWrite((DB)db);
		}

		return true;
	}

	public void doTransactionRead(DB db) {
		// choose a random key
		int keynum;
		do {
			keynum = keychooser.nextInt();
		} while (keynum > transactioninsertkeysequence.lastInt());

		if (!orderedinserts) {
			keynum = Utils.hash(keynum);
		}
		String keyname = "user" + keynum;

		HashSet<String> fields = null;

		if (!Config.getConfig().read_all_fields) {
			// read a random field
			String fieldname = "field" + fieldchooser.nextString();

			fields = new HashSet<String>();
			fields.add(fieldname);
		}

		db.read(Config.getConfig().table_name, keyname, fields, new HashMap<String, String>());
	}

	public void doTransactionReadModifyWrite(DB db) {
		// choose a random key
		int keynum;
		do {
			keynum = keychooser.nextInt();
		} while (keynum > transactioninsertkeysequence.lastInt());

		if (!orderedinserts) {
			keynum = Utils.hash(keynum);
		}
		String keyname = "user" + keynum;

		HashSet<String> fields = null;

		if (!Config.getConfig().read_all_fields) {
			// read a random field
			String fieldname = "field" + fieldchooser.nextString();

			fields = new HashSet<String>();
			fields.add(fieldname);
		}

		HashMap<String, String> values = new HashMap<String, String>();

		if (Config.getConfig().write_all_fields) {
			// new data for all the fields
			for (int i = 0; i < Config.getConfig().field_count; i++) {
				String fieldname = "field" + i;
				String data = Utils.ASCIIString(Config.getConfig().field_length);
				values.put(fieldname, data);
			}
		} else {
			// update a random field
			String fieldname = "field" + fieldchooser.nextString();
			String data = Utils.ASCIIString(Config.getConfig().field_length);
			values.put(fieldname, data);
		}

		// do the transaction

		long st = System.currentTimeMillis();

		db.read(Config.getConfig().table_name, keyname, fields, new HashMap<String, String>());

		db.update(Config.getConfig().table_name, keyname, values);

		long en = System.currentTimeMillis();

		Measurements.getMeasurements().measure("READ-MODIFY-WRITE",
				(int) (en - st));
	}

	public void doTransactionScan(DB db) {
		// choose a random key
		int keynum;
		do {
			keynum = keychooser.nextInt();
		} while (keynum > transactioninsertkeysequence.lastInt());

		if (!orderedinserts) {
			keynum = Utils.hash(keynum);
		}
		String startkeyname = "user" + keynum;

		// choose a random scan length
		int len = scanlength.nextInt();

		HashSet<String> fields = null;

		if (!Config.getConfig().read_all_fields) {
			// read a random field
			String fieldname = "field" + fieldchooser.nextString();

			fields = new HashSet<String>();
			fields.add(fieldname);
		}

		db.scan(Config.getConfig().table_name, startkeyname, len, fields,
				new Vector<HashMap<String, String>>());
	}

	public void doTransactionUpdate(DB db) {
		// choose a random key
		int keynum;
		do {
			keynum = keychooser.nextInt();
		} while (keynum > transactioninsertkeysequence.lastInt());

		if (!orderedinserts) {
			keynum = Utils.hash(keynum);
		}
		String keyname = "user" + keynum;

		HashMap<String, String> values = new HashMap<String, String>();

		if (Config.getConfig().write_all_fields) {
			// new data for all the fields
			for (int i = 0; i < Config.getConfig().field_count; i++) {
				String fieldname = "field" + i;
				String data = Utils.ASCIIString(Config.getConfig().field_length);
				values.put(fieldname, data);
			}
		} else {
			// update a random field
			String fieldname = "field" + fieldchooser.nextString();
			String data = Utils.ASCIIString(Config.getConfig().field_length);
			values.put(fieldname, data);
		}

		db.update(Config.getConfig().table_name, keyname, values);
	}

	public void doTransactionInsert(DB db) {
		// choose the next key
		int keynum = transactioninsertkeysequence.nextInt();
		if (!orderedinserts) {
			keynum = Utils.hash(keynum);
		}
		String dbkey = "user" + keynum;

		HashMap<String, String> values = new HashMap<String, String>();
		for (int i = 0; i < Config.getConfig().field_count; i++) {
			String fieldkey = "field" + i;
			String data = Utils.ASCIIString(Config.getConfig().field_length);
			values.put(fieldkey, data);
		}
		db.insert(Config.getConfig().table_name, dbkey, values);
	}
}
