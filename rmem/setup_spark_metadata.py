import os
import time

def beeline(query):
  os.system("/root/spark/bin/beeline -u jdbc:hive2://localhost:10000 -n root -e \"%s\"" % query)

os.system("/root/spark/sbin/start-thriftserver.sh")

time.sleep(30)

beeline("DROP TABLE IF EXISTS rankings")
beeline(
  "CREATE EXTERNAL TABLE rankings (pageURL STRING, pageRank INT, " \
  "avgDuration INT) ROW FORMAT DELIMITED FIELDS TERMINATED BY \\\",\\\" " \
  "STORED AS TEXTFILE LOCATION \\\"/user/spark/benchmark/rankings\\\";")

beeline("DROP TABLE IF EXISTS uservisits;")
beeline(
  "CREATE EXTERNAL TABLE uservisits (sourceIP STRING,destURL STRING," \
  "visitDate STRING,adRevenue DOUBLE,userAgent STRING,countryCode STRING," \
  "languageCode STRING,searchWord STRING,duration INT ) " \
  "ROW FORMAT DELIMITED FIELDS TERMINATED BY \\\",\\\" " \
  "STORED AS TEXTFILE LOCATION \\\"/user/spark/benchmark/uservisits\\\";")

beeline("DROP TABLE IF EXISTS documents;")
beeline(
  "CREATE EXTERNAL TABLE documents (line STRING) STORED AS TEXTFILE " \
  "LOCATION \\\"/user/spark/benchmark/crawl\\\";")

