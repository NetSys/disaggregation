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

import com.yahoo.ycsb.UnknownDataStoreException;

/**
 * Creates a DB layer by dynamically classloading the specified DB class.
 */
public class MemcachedFactory {
	@SuppressWarnings("rawtypes")
	public static Memcached newMemcached(String memcachedname) throws UnknownDataStoreException {
		ClassLoader classLoader = MemcachedFactory.class.getClassLoader();

		Memcached ret = null;

		try {
			Class memcachedclass = classLoader.loadClass(memcachedname);
			// System.out.println("dbclass.getName() = " + dbclass.getName());

			ret = (Memcached) memcachedclass.newInstance();
		} catch (ClassCastException e) {
			throw new UnknownDataStoreException(e); 
		} catch (ClassNotFoundException e) {
			throw new UnknownDataStoreException(e);
		} catch (InstantiationException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		} catch (IllegalAccessException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}

		return new MemcachedWrapper(ret);
	}

}
