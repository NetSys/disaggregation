# Copyright 2013 The Regents of The University California
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Run a single query from the big data benchmark on a remote EC2 cluster.

   This will execute a single query from the benchmark multiple times
   and output percentile results. Note that to run an entire suite of
   queries, you'll need to wrap this script and call run multiple times.
"""

import subprocess
import sys
from sys import stderr
from optparse import OptionParser
import os
import time
import datetime
import re
import multiprocessing
from StringIO import StringIO
import shutil

# A scratch directory on your filesystem
LOCAL_TMP_DIR = "/tmp"

### Benchmark Queries ###
TMP_TABLE = "result"
TMP_TABLE_CACHED = "result_cached"
CLEAN_QUERY = "DROP TABLE %s;" % TMP_TABLE

# TODO: Factor this out into a separate file
QUERY_1a_HQL = "SELECT pageURL, pageRank FROM rankings WHERE pageRank > 1000"
QUERY_1b_HQL = QUERY_1a_HQL.replace("1000", "100")
QUERY_1c_HQL = QUERY_1a_HQL.replace("1000", "10")

QUERY_2a_HQL = "SELECT SUBSTR(sourceIP, 1, 8), SUM(adRevenue) FROM " \
                 "uservisits GROUP BY SUBSTR(sourceIP, 1, 8)"
QUERY_2b_HQL = QUERY_2a_HQL.replace("8", "10")
QUERY_2c_HQL = QUERY_2a_HQL.replace("8", "12")

QUERY_3a_HQL = """SELECT sourceIP,
                          sum(adRevenue) as totalRevenue,
                          avg(pageRank) as pageRank
                   FROM
                     rankings R JOIN
                     (SELECT sourceIP, destURL, adRevenue
                      FROM uservisits UV
                      WHERE UV.visitDate > "1980-01-01"
                      AND UV.visitDate < "1980-04-01")
                      NUV ON (R.pageURL = NUV.destURL)
                   GROUP BY sourceIP
                   ORDER BY totalRevenue DESC
                   LIMIT 1"""
QUERY_3a_HQL = " ".join(QUERY_3a_HQL.replace("\n", "").split())
QUERY_3b_HQL = QUERY_3a_HQL.replace("1980-04-01", "1983-01-01")
QUERY_3c_HQL = QUERY_3a_HQL.replace("1980-04-01", "2010-01-01")

QUERY_4_HQL = """UNCACHE TABLE url_counts_partial;
                 UNCACHE TABLE url_counts_total;
                 DROP TABLE IF EXISTS url_counts_partial;
                 CREATE TABLE url_counts_partial AS
                   SELECT TRANSFORM (line)
                   USING "python /root/url_count.py" as (sourcePage,
                     destPage, count) from documents;
                 DROP TABLE IF EXISTS url_counts_total;
                 CREATE TABLE url_counts_total AS
                   SELECT SUM(count) AS totalCount, destpage
                   FROM url_counts_partial GROUP BY destpage;"""
QUERY_4_HQL = " ".join(QUERY_4_HQL.replace("\n", "").split())

QUERY_4_HQL_HIVE_UDF = """DROP TABLE IF EXISTS url_counts_partial;
                 CREATE TABLE url_counts_partial AS
                   SELECT TRANSFORM (line)
                   USING "python /tmp/url_count.py" as (sourcePage,
                     destPage, count) from documents;
                 DROP TABLE IF EXISTS url_counts_total;
                 CREATE TABLE url_counts_total AS
                   SELECT SUM(count) AS totalCount, destpage
                   FROM url_counts_partial GROUP BY destpage;"""
QUERY_4_HQL_HIVE_UDF = " ".join(QUERY_4_HQL_HIVE_UDF.replace("\n", "").split())

QUERY_1_PRE = "CREATE TABLE %s (pageURL STRING, pageRank INT);" % TMP_TABLE
QUERY_2_PRE = "CREATE TABLE %s (sourceIP STRING, adRevenue DOUBLE);" % TMP_TABLE
QUERY_3_PRE = "CREATE TABLE %s (sourceIP STRING, " \
    "adRevenue DOUBLE, pageRank DOUBLE);" % TMP_TABLE

QUERY_1a_SQL = QUERY_1a_HQL
QUERY_1b_SQL = QUERY_1b_HQL
QUERY_1c_SQL = QUERY_1c_HQL

QUERY_2a_SQL = QUERY_2a_HQL.replace("SUBSTR", "SUBSTRING")
QUERY_2b_SQL = QUERY_2b_HQL.replace("SUBSTR", "SUBSTRING")
QUERY_2c_SQL = QUERY_2c_HQL.replace("SUBSTR", "SUBSTRING")
QUERY_3a_SQL = """SELECT sourceIP, totalRevenue, avgPageRank
                    FROM
                      (SELECT sourceIP,
                              AVG(pageRank) as avgPageRank,
                              SUM(adRevenue) as totalRevenue
                      FROM Rankings AS R, UserVisits AS UV
                      WHERE R.pageURL = UV.destinationURL
                      AND UV.visitDate
                        BETWEEN Date('1980-01-01') AND Date('1980-04-01')
                      GROUP BY UV.sourceIP)
                   ORDER BY totalRevenue DESC LIMIT 1""".replace("\n", "")
QUERY_3a_SQL = " ".join(QUERY_3a_SQL.replace("\n", "").split())
QUERY_3b_SQL = QUERY_3a_SQL.replace("1980-04-01", "1983-01-01")
QUERY_3c_SQL = QUERY_3a_SQL.replace("1980-04-01", "2010-01-01")

def create_as(query):
  return "CREATE TABLE %s AS %s;" % (TMP_TABLE, query)
def insert_into(query):
  return "INSERT INTO TABLE %s %s;" % (TMP_TABLE, query)
def count(query):
  return query
  return "SELECT COUNT(*) FROM (%s) q;" % query

IMPALA_MAP = {'1a': QUERY_1_PRE, '1b': QUERY_1_PRE, '1c': QUERY_1_PRE,
              '2a': QUERY_2_PRE, '2b': QUERY_2_PRE, '2c': QUERY_2_PRE,
              '3a': QUERY_3_PRE, '3b': QUERY_3_PRE, '3c': QUERY_3_PRE}

TEZ_MAP =    {'1a':(count(QUERY_1a_HQL),), '1b':(count(QUERY_1b_HQL),), '1c': (count(QUERY_1c_HQL),),
              '2a':(count(QUERY_2a_HQL),), '2b':(count(QUERY_2b_HQL),), '2c': (count(QUERY_2c_HQL),),
              '3a':(count(QUERY_3a_HQL),), '3b':(count(QUERY_3b_HQL),), '3c': (count(QUERY_3c_HQL),)}

QUERY_MAP = {
             '1a':  (create_as(QUERY_1a_HQL), insert_into(QUERY_1a_HQL),
                     create_as(QUERY_1a_SQL)),
             '1b':  (create_as(QUERY_1b_HQL), insert_into(QUERY_1b_HQL),
                     create_as(QUERY_1b_SQL)),
             '1c':  (create_as(QUERY_1c_HQL), insert_into(QUERY_1c_HQL),
                     create_as(QUERY_1c_SQL)),
             '2a': (create_as(QUERY_2a_HQL), insert_into(QUERY_2a_HQL),
                    create_as(QUERY_2a_SQL)),
             '2b': (create_as(QUERY_2b_HQL), insert_into(QUERY_2b_HQL),
                    create_as(QUERY_2b_SQL)),
             '2c': (create_as(QUERY_2c_HQL), insert_into(QUERY_2c_HQL),
                    create_as(QUERY_2c_SQL)),
             '3a': (create_as(QUERY_3a_HQL), insert_into(QUERY_3a_HQL),
                    create_as(QUERY_3a_SQL)),
             '3b': (create_as(QUERY_3b_HQL), insert_into(QUERY_3b_HQL),
                    create_as(QUERY_3b_SQL)),
             '3c': (create_as(QUERY_3c_HQL), insert_into(QUERY_3c_HQL),
                    create_as(QUERY_3c_SQL)),
             '4':  (QUERY_4_HQL, None, None),
             '4_HIVE':  (QUERY_4_HQL_HIVE_UDF, None, None)}

# Turn a given query into a version using cached tables
def make_input_cached(query):
  return query.replace("uservisits", "uservisits_cached") \
              .replace("rankings", "rankings_cached") \
              .replace("url_counts_partial", "url_counts_partial_cached") \
              .replace("url_counts_total", "url_counts_total_cached") \
              .replace("documents", "documents_cached")

# Turn a given query into one that creats cached tables
def make_output_cached(query):
  return query.replace(TMP_TABLE, TMP_TABLE_CACHED)

### Runner ###
def parse_args():
  parser = OptionParser(usage="run_query.py [options]")

  parser.add_option("-m", "--impala", action="store_true", default=False,
      help="Whether to include Impala")
  parser.add_option("-s", "--spark", action="store_true", default=False,
      help="Whether to include Spark SQL")
  parser.add_option("-r", "--redshift", action="store_true", default=False,
      help="Whether to include Redshift")
  parser.add_option("--shark", action="store_true", default=False,
      help="Whether to include Shark")
  parser.add_option("--hive", action="store_true", default=False,
      help="Whether to include Hive")
  parser.add_option("--tez", action="store_true", default=False,
      help="Use in conjunction with --hive")
  parser.add_option("--hive-cdh", action="store_true", default=False,
      help="Hive on CDH cluster")

  parser.add_option("-g", "--spark-no-cache", action="store_true",
      default=False, help="Disable caching in Spark SQL")
  parser.add_option("--shark-no-cache", action="store_true",
      default=False, help="Disable caching in Shark")
  parser.add_option("--impala-use-hive", action="store_true",
      default=False, help="Use Hive for query executio on Impala nodes")
  parser.add_option("-t", "--reduce-tasks", type="int", default=200,
      help="Number of reduce tasks in Shark & Spark SQL")
  parser.add_option("-z", "--clear-buffer-cache", action="store_true",
      default=False, help="Clear disk buffer cache between query runs")

  parser.add_option("-a", "--impala-hosts",
      help="Hostnames of Impala nodes (comma seperated)")
  parser.add_option("-b", "--spark-host",
      help="Hostname of Spark master node")
  parser.add_option("-c", "--redshift-host",
      help="Hostname of Redshift ODBC endpoint")
  parser.add_option("--shark-host",
      help="Hostname of Shark master node")
  parser.add_option("--hive-host",
      help="Hostname of Hive master node")
  parser.add_option("--hive-slaves",
      help="Hostnames of Hive slaves (comma seperated)")

  parser.add_option("-x", "--impala-identity-file",
      help="SSH private key file to use for logging into Impala node")
  parser.add_option("-y", "--spark-identity-file",
      help="SSH private key file to use for logging into Spark node")
  parser.add_option("--shark-identity-file",
      help="SSH private key file to use for logging into Shark node")
  parser.add_option("--hive-identity-file",
      help="SSH private key file to use for logging into Hive node")
  parser.add_option("-u", "--redshift-username",
      help="Username for Redshift ODBC connection")
  parser.add_option("-p", "--redshift-password",
      help="Password for Redshift ODBC connection")
  parser.add_option("-e", "--redshift-database",
      help="Database to use in Redshift")
  parser.add_option("--num-trials", type="int", default=10,
      help="Number of trials to run for this query")
  parser.add_option("--prefix", type="string", default="",
      help="Prefix result files with this string")
  parser.add_option("--shark-mem", type="string", default="24g",
      help="How much executor memory shark nodes should use")

  parser.add_option("-q", "--query-num", default="1a",
                    help="Which query to run in benchmark: " \
                    "%s" % ", ".join(QUERY_MAP.keys()))

  (opts, args) = parser.parse_args()

  if not (opts.impala or opts.spark or opts.shark or opts.redshift or opts.hive or opts.hive_cdh):
    parser.print_help()
    sys.exit(1)


  if opts.query_num not in QUERY_MAP:
    print >> stderr, "Unknown query number: %s" % opts.query_num
    sys.exit(1)

  return opts

# Run a command on a host through ssh, throwing an exception if ssh fails
def ssh(command):
  print command
  return os.system(command)

# Copy a file to a given host through scp, throwing an exception if scp fails
def scp_to(local_file, remote_file):
  shutil.copy(local_file, remote_file)

# Copy a file to a given host through scp, throwing an exception if scp fails
def scp_from(remote_file, local_file):
  shutil.copy(remote_file, local_file)

def run_spark_benchmark(opts):
  def ssh_spark(command):
    command = "source /root/.bash_profile; %s" % command
    ssh(command)

  local_clean_query = CLEAN_QUERY
  local_query_map = QUERY_MAP

  prefix = str(time.time()).split(".")[0]
  query_file_name = "%s_workload.sh" % prefix
  local_query_file = os.path.join(LOCAL_TMP_DIR, query_file_name)
  query_file = open(local_query_file, 'w')
  remote_result_file = "/mnt/%s_results" % prefix
  remote_tmp_file = "/mnt/%s_out" % prefix
  remote_query_file = "/mnt/%s" % query_file_name

  runner = "/root/spark/bin/beeline -u jdbc:hive2://localhost:10000 -n root"

  # Two modes here: Spark SQL Mem and Spark SQL Disk. If using Spark SQL disk use
  # uncached tables. If using Spark SQL Mem, used cached tables.

  query_list = "set spark.sql.codegen=true; set spark.sql.shuffle.partitions = %s;" % opts.reduce_tasks
  # Comment out for uncompressed output.
  query_list += "SET hive.exec.compress.output=True;SET io.seqfile.compression.type=BLOCK;"

  # Create cached queries for Spark SQL Mem
  if not opts.spark_no_cache:

    # Set up cached tables
    if False:
# skip for now!! Done manually.
      if '4' in opts.query_num:
        # Query 4 uses entirely different tables
        query_list += """
                      CACHE TABLE documents;
                      """
      else:
        query_list += """
                      CACHE TABLE rankings;
                      """
        if '1' not in opts.query_num:
          # For query 1, only need the rankings table.
          query_list += """
                        CACHE TABLE uservisits;
                        """

  if '4' not in opts.query_num:
    query_list += local_clean_query
  query_list += local_query_map[opts.query_num][0]

  # Store the result only in mem
  if not opts.spark_no_cache:
    query_list = query_list.replace("CREATE TABLE", "CACHE TABLE")

  query_list = re.sub("\s\s+", " ", query_list.replace('\n', ' '))

  print "\nQuery:"
  print query_list.replace(';', ";\n")

  if opts.clear_buffer_cache:
    print "Writing command to clear buffer cache"
    query_file.write("ephemeral-hdfs/sbin/slaves.sh /root/spark-ec2/clear-cache.sh\n")

  query_file.write(
    "%s %s > %s 2>&1\n" % (runner, " ".join("-e '%s'" % q.strip() for q in query_list.split(";") if q.strip()), remote_tmp_file))

  query_file.write(
      "cat %s | grep seconds >> %s\n" % (
        remote_tmp_file, remote_result_file))

  query_file.close()

  print "Copying files to Spark"
  scp_to(local_query_file, remote_query_file)
  ssh_spark("chmod 775 %s" % remote_query_file)

  # Run benchmark
  print "Running remote benchmark..."

  # Collect results
  results = []
  contents = []

  for i in range(opts.num_trials):
    print "Query %s : Trial %i" % (opts.query_num, i+1)
    ssh_spark("%s" % remote_query_file)
    local_results_file = os.path.join(LOCAL_TMP_DIR, "%s_results" % prefix)
    scp_from("/mnt/%s_results" % prefix, local_results_file)
    content = open(local_results_file).readlines()
    all_times = [float(x.split("(")[1].split(" ")[0]) for x in content]

    if '4' in opts.query_num:
      query_times = all_times[-4:]
      part_a = query_times[1]
      part_b = query_times[3]
      print "Parts: %s, %s" % (part_a, part_b)
      result = float(part_a) + float(part_b)
    else:
      result = all_times[-1] # Only want time of last query

    print "Result: ", result
    print "Raw Times: ", content

    results.append(result)
    contents.append(content)

    # Clean-up
    #ssh_shark("rm /mnt/%s*" % prefix)
    print "Clean Up...."
    ssh_spark("rm /mnt/%s_results" % prefix)
    os.remove(local_results_file)

  os.remove(local_query_file)

  return results, contents

def get_percentiles(in_list):
  def get_pctl(lst, pctl):
    return lst[int(len(lst) * pctl)]
  in_list = sorted(in_list)
  return "%s\t%s\t%s" % (
    get_pctl(in_list, 0.05),
    get_pctl(in_list, .5),
    get_pctl(in_list, .95)
  )

def ssh_ret_code(host, user, id_file, cmd):
  try:
    return ssh(host, user, id_file, cmd)
  except subprocess.CalledProcessError as e:
    return e.returncode

def ensure_spark_stopped_on_slaves(slaves):
  stop = False
  while not stop:
    cmd = "jps | grep ExecutorBackend"
    ret_vals = map(lambda s: ssh_ret_code(s, "root", opts.spark_identity_file, cmd), slaves)
    print ret_vals
    if 0 in ret_vals:
      print "Spark is still running on some slaves... sleeping"
      cmd = "jps | grep ExecutorBackend | cut -d \" \" -f 1 | xargs -rn1 kill -9"
      map(lambda s: ssh_ret_code(s, "root", opts.spark_identity_file, cmd), slaves)
      time.sleep(2)
    else:
      stop = True


def main():
  global opts
  opts = parse_args()

  print "Query %s:" % opts.query_num

  if opts.spark:
    results, contents = run_spark_benchmark(opts)
 

 

  if opts.spark:
    if opts.spark_no_cache:
      fname = "spark_disk"
    else:
      fname = "spark_mem"
  else:
    print "error"
    quit()
  


  fname = opts.prefix + fname

  def prettylist(lst):
    return ",".join([str(k) for k in lst])

  output = StringIO()
  outfile = open('results_%s_%s_%s' % (fname, opts.query_num, datetime.datetime.now()), 'w')

  try:
    if not opts.redshift:
      print >> output, "Contents: \n%s" % str(prettylist(contents))
    print >> output, "=================================="
    print >> output, "Results: %s" % prettylist(results)
    print >> output, "Percentiles: %s" % get_percentiles(results)
    print >> output, "Best: %s"  % min(results)
    if not opts.redshift:
      print >> output, "Contents: \n%s" % str(prettylist(contents))
    print output.getvalue()
    print >> outfile, output.getvalue()
  except:
    print output.getvalue()
    print >> outfile, output.getvalue()

  output.close()
  outfile.close()

if __name__ == "__main__":
  main()
