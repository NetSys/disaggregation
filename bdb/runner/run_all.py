import random
import subprocess
import sys

COMMAND_TEMPLATE = ("./run-query.sh --shark --shark-host=%s --shark-identity-file=%s " +
  #"--query-num=%s --num-trials=%d --shark-no-cache --clear-buffer-cache --use-sharkserver")
  "--query-num=%s --num-trials=%d --shark-no-cache --clear-buffer-cache --use-sharkserver")

queries = ["1a", "1b", "1c", "2a", "2b", "2c", "3a", "3b", "3c", "4"]
#queries = ["1a", "2a", "3a", "4"]
#queries = ["1a", "1b", "1c", "2a", "2b", "2c", "3a", "3b", "3c"]
#queries = ["1a", "1b", "1c"]
#queries = ["4"]
#queries = ["3a", "3b", "3c"]

def main(args):
  if len(args) != 3:
    print "Usage: run_all.py shark_host identity_file num_trials"
    exit(1)
  shark_host = args[0]
  identity_file = args[1]
  num_trials = int(args[2])

  print "Running %d trials of each query through master %s" % (num_trials, shark_host)

  for i in range(num_trials):
    random.shuffle(queries)
    for query in queries:
      command = COMMAND_TEMPLATE % (shark_host, identity_file, query, 1)
      print "Running query %s using command \"%s\"" % (query, command)
      subprocess.check_call(command, shell=True)

if __name__ == "__main__":
  main(sys.argv[1:])
