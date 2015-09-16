package com.yahoo.ycsb.db;

import java.io.IOException;
import java.net.InetAddress;
import java.net.InetSocketAddress;
import java.net.UnknownHostException;
import java.util.Random;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.Future;
import java.io.File;
import java.io.FileInputStream;
import java.lang.StringBuilder;
import java.lang.Exception;

import net.spy.memcached.CASResponse;
import net.spy.memcached.MemcachedClient;
import net.spy.memcached.BinaryConnectionFactory;
import net.spy.memcached.AddrUtil;

import com.yahoo.ycsb.Config;
import com.yahoo.ycsb.memcached.Memcached;


public class SpymemcachedClient extends Memcached {
	MemcachedClient client;
	
	public static long endtime;
	
	Random random;
	boolean verbose;
	int todelay;
  int err_count;

	public SpymemcachedClient() {
		random = new Random();
		todelay = 0;
    err_count = 0;
	}
	
	/**
	 * Initialize any state for this DB. Called once per DB instance; there is
	 * one DB instance per client thread.
	 */
	public void init() {
		int membaseport = Config.getConfig().memcached_port;
		String addr_file = Config.getConfig().memcached_address;


    String[] lines = null;
    try{
      File file = new File(addr_file);
      FileInputStream fis = new FileInputStream(file);
      byte[] data = new byte[(int) file.length()];
      fis.read(data);
      fis.close();

      String str = new String(data, "UTF-8");
      lines = str.split("\n");

    }
    catch(Exception e)
    {
      System.out.println("oops");
    }

    StringBuilder sb = new StringBuilder();
    for(int i = 0; i < lines.length; i++){
      sb.append(lines[i] + ":" + membaseport + " ");
    }
		
    System.out.println("Addresses:" + sb.toString());

		try {
      //local mode
      //client = new MemcachedClient(new BinaryConnectionFactory(), AddrUtil.getAddresses("localhost:" + membaseport));

      //dist mode
      client = new MemcachedClient(new BinaryConnectionFactory(), AddrUtil.getAddresses(sb.toString()));
		} catch (UnknownHostException e) {
			e.printStackTrace();
		} catch (IOException e1) {
			e1.printStackTrace();
		}
	}
	
	public void cleanup() {
		if (client.isAlive())
			client.shutdown();
	}
	
	@Override
	public int add(String key, Object value) {
		try {
			if (!client.add(key, 0, value).get().booleanValue()) {
        if(err_count < 100){
				  System.out.println("ADD: error getting data");
          err_count++;
        }
				return -1;
			}
		} catch (InterruptedException e) {
			System.out.println("ADD Interrupted");
		} catch (ExecutionException e) {
			System.out.println("ADD Execution");
		} catch (RuntimeException e) {
			System.out.println("ADD Runtime");
		}
		return 0;
	}
	
	@Override
	public int get(String key, Object value) {
		long st = System.currentTimeMillis();
		Future<Object> f = client.asyncGet(key);
		//long time = System.nanoTime();
		try {
			if (f.get() == null) {
        if(err_count < 100){
				  System.out.println("GET: error getting data");
          err_count++;
        }
				return -1;
			}
		} catch (InterruptedException e) {
			System.out.println("GET Interrupted");
		} catch (ExecutionException e) {
			System.out.println("GET Execution");
			e.printStackTrace();
			return -2;
		} catch (RuntimeException e) {
			System.out.println("GET Runtime: " + (System.currentTimeMillis() - st));
			return -3;
		}
		//System.out.println("Start: " + time);
		//System.out.println("Start: " + endtime);
		//System.out.println("Spy latency: " + ((endtime - time)/1000));
		return 0;
	}
	/*
	public Future<Object> asyncGet(final String key) {
		return asyncGet(key, client.getTranscoder());
	}
	
	public <T> Future<T> asyncGet(final String key, final Transcoder<T> tc) {
		final CountDownLatch latch=new CountDownLatch(1);
		final GetFuture<T> rv=new GetFuture<T>(latch, 1000);
		
		Operation op=client.opFact.get(key,
				new GetOperation.Callback() {
			private Future<T> val=null;
			public void receivedStatus(OperationStatus status) {
				rv.set(val);
				
			}
			public void gotData(String k, int flags, byte[] data) {
				assert key.equals(k) : "Wrong key returned";
				val=client.tcService.decode(tc,
					new CachedData(flags, data, tc.getMaxSize()));
			}
			
			public void complete() {
				SpymemcachedClient.endtime = System.nanoTime();
				System.out.println("Complete");
				latch.countDown();
			}});
		rv.setOperation(op);
		client.addOp(key, op);
		return rv;
	}*/
	
	
	

	@Override
	public int set(String key, Object value) {
		try {
			if (!client.set(key, 0, value).get().booleanValue()) {
        if(err_count < 100){
				  System.out.println("SET: error getting data");
          err_count++;
        }
				return -1;
			}
		} catch (InterruptedException e) {
			System.out.println("SET Interrupted");
		} catch (ExecutionException e) {
			System.out.println("SET Execution");
		} catch (RuntimeException e) {
			System.out.println("SET Runtime");
		}
		return 0;
	}
	
	private byte[] ipv4AddressToByte(String address) {
		byte[] b = new byte[4];
		String[] str = address.split("\\.");
		b[0] = Integer.valueOf(str[0]).byteValue();
		b[1] = Integer.valueOf(str[1]).byteValue();
		b[2] = Integer.valueOf(str[2]).byteValue();
		b[3] = Integer.valueOf(str[3]).byteValue();
		return b;
	}

	@Override
	public int append(String key, long cas, Object value) {
		try {
			if (!client.append(cas, key, value).get().booleanValue())
        if(err_count < 100){
				  System.out.println("APPEND: error getting data");
          err_count++;
        }
				return -1;
		} catch (InterruptedException e) {
			System.out.println("APPEND Interrupted");
		} catch (ExecutionException e) {
			System.out.println("APPEND Execution");
		} catch (RuntimeException e) {
			System.out.println("APPEND Runtime");
		}
		return 0;
	}

	@Override
	public int cas(String key, long cas, Object value) {
		if (!client.cas(key, cas, value).equals(CASResponse.OK)) {
      if(err_count < 100){
			  System.out.println("CAS: error getting data");
        err_count++;
      }
			return -1;
		}
		return 0;
	}

	@Override
	public int decr(String key, Object value) {
		return 0;
	}

	@Override
	public int delete(String key) {
		return 0;
	}

	@Override
	public int incr(String key, Object value) {
		return 0;
	}

	@Override
	public long gets(String key) {
		long cas = client.gets(key).getCas();
		if (cas < 0) {
      if(err_count < 100){
			  System.out.println("GETS: error getting data");
        err_count++;
      }
			return -1;
		}
		return cas;
	}

	@Override
	public int prepend(String key, long cas, Object value) {
		try {
			if (!client.prepend(cas, key, value).get().booleanValue())
				return -1;
		} catch (InterruptedException e) {
			System.out.println("PREPEND Interrupted");
		} catch (ExecutionException e) {
			System.out.println("PREPEND Execution");
		} catch (RuntimeException e) {
			System.out.println("PREPEND Runtime");
		}
		return 0;
	}

	@Override
	public int replace(String key, Object value) {
		try {
			if (!client.replace(key, 0, value).get().booleanValue()) {
        if(err_count < 100){
				  System.out.println("REPLACE: error getting data");
          err_count++;
        }
				return -1;
			}
		} catch (InterruptedException e) {
			System.out.println("REPLACE Interrupted");
		} catch (ExecutionException e) {
			System.out.println("REPLACE Execution");
		} catch (RuntimeException e) {
			System.out.println("REPLACE Runtime");
		}
		return 0;
	}
	
	public static void main(String args[]) {
		SpymemcachedClient client = new SpymemcachedClient();
		client.init();
	}

	@Override
	public int update(String key, Object value) {
		return set(key, value);
	}
}
