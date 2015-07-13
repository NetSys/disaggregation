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

package com.yahoo.ycsb.memcached;

import com.yahoo.ycsb.DataStore;

/**
 * A layer for accessing a database to be benchmarked. Each thread in the client
 * will be given its own instance of whatever DB class is to be used in the
 * test. This class should be constructed using a no-argument constructor, so we
 * can load it dynamically. Any argument-based initialization should be done by
 * init().
 * 
 * Note that YCSB does not make any use of the return codes returned by this
 * class. Instead, it keeps a count of the return values and presents them to
 * the user.
 * 
 * The semantics of methods such as insert, update and delete vary from database
 * to database. In particular, operations may or may not be durable once these
 * methods commit, and some systems may return 'success' regardless of whether
 * or not a tuple with a matching key existed before the call. Rather than
 * dictate the exact semantics of these methods, we recommend you either
 * implement them to match the database's default semantics, or the semantics of
 * your target application. For the sake of comparison between experiments we
 * also recommend you explain the semantics you chose when presenting
 * performance results.
 */
public abstract class Memcached extends DataStore{

	/**
	 * Add a value in the database. Any key/value pair in the specified
	 * value Object will be added as a value to a specific key.
	 * 
	 * @param key
	 *            The key of the value to add.          		
	 * @param value
	 *            An Object to use as the key's value
	 * @return Zero on success, a non-zero error code on error. See this class's
	 *         description for a discussion of error codes.
	 */
	public abstract int add(String key, Object value);
	
	/**
	 * Append a value in the database. Any key/value pair in the specified
	 * value Object will be appended onto the value with the specified key.
	 * 
	 * @param key
	 *            The key of the value to be appended to.
	 * @param cas
	 * 			  The cas value needed to do the append 
	 * @param value
	 *            An Object to use as the key's value
	 * @return Zero on success, a non-zero error code on error. See this class's
	 *         description for a discussion of error codes.
	 */
	public abstract int append(String key, long cas, Object value);
	
	/**
	 * Does a Create and store operation.
	 * 
	 * @param key
	 *            The key of the value to do the cas.
	 * @param cas
	 * 			  The cas value needed to do the append 
	 * @param value
	 *            An Object to use as the key's value
	 * @return Zero on success, a non-zero error code on error. See this class's
	 *         description for a discussion of error codes.
	 */
	public abstract int cas(String key, long cas, Object value);
	
	/**
	 * Decrement a value in the database.
	 * 
	 * @param key
	 *            The key of the value to be decremented.
	 * @param value
	 *            An Object to use as the key's value
	 * @return Zero on success, a non-zero error code on error. See this class's
	 *         description for a discussion of error codes.
	 */
	public abstract int decr(String key, Object value);
	
	/**
	 * Delete a value from the database.
	 * 
	 * @param key
	 *            The key of the value to be deleted.
	 * @return Zero on success, a non-zero error code on error. See this class's
	 *         description for a discussion of error codes.
	 */
	public abstract int delete(String key);
	
	/**
	 * Increment a value in the database.
	 * 
	 * @param key
	 *            The key of the value to be incremented.
	 * @param value
	 *            An Object to use as the key's value
	 * @return Zero on success, a non-zero error code on error. See this class's
	 *         description for a discussion of error codes.
	 */
	public abstract int incr(String key, Object value);
	
	/**
	 * Get a value from the database. Any key/value pair in the specified
	 * value Object will be check against the value returned from the database.
	 * 
	 * @param key
	 *            The key of the value to get.
	 * @param value
	 *            The Object that the key should contain
	 * @return Zero on success, a non-zero error code on error. See this class's
	 *         description for a discussion of error codes.
	 */
	public abstract int get(String key, Object value);
	
	/**
	 * Get a CAS identifier for a value in the database
	 * 
	 * @param key
	 *            The key of the value to get a CAS identifier for
	 * @return The CAS identifier on success, a non-zero error code on error. See this class's
	 *         description for a discussion of error codes.
	 */
	public abstract long gets(String key);
	
	/**
	 * Prepends a value to a specific keys current value
	 * 
	 * @param key
	 *            The key of the value to prepend.
	 * @param value
	 *            The Object to prepend to the current key
	 * @return Zero on success, a non-zero error code on error. See this class's
	 *         description for a discussion of error codes.
	 */
	public abstract int prepend(String key, long cas, Object value);
	
	/**
	 * Replaces the current value of a key if the key already exists
	 * 
	 * @param key
	 *            The key of the value to replace.
	 * @param cas
	 * 			  The cas value needed to do the append 
	 * @param value
	 *            The Object to replace the old value with
	 * @return Zero on success, a non-zero error code on error. See this class's
	 *         description for a discussion of error codes.
	 */
	public abstract int replace(String key, Object value);
	
	/**
	 * Set a record in the database. Any key/value pair in the specified
	 * values Object will be written into the key with the specified value.
	 * 
	 * @param key
	 *            The key of the value to insert.
	 * @param value
	 *            An Object to use as the key's value
	 * @return Zero on success, a non-zero error code on error. See this class's
	 *         description for a discussion of error codes.
	 */
	public abstract int set(String key, Object value);
	
	public abstract int update(String key, Object value);

}
