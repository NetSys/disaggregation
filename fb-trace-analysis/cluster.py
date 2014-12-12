from task import *
from job import *
from lib import *
import sys
import random

class Cluster:
  def __init__(self, file="../../ramdisk/24h.txt", get_server_list = True):
    split_path = file.split("/")
    self.name = split_path[len(split_path)-1].replace(".txt","")
    self.jobs = {}
    self.servers = {}
    self.servers_list = []
    self.total_tasks = 0
    self.total_map_tasks = 0
    self.total_red_tasks = 0
    trace = open(file)

    for line in trace:
      task = Task(line)
      self.total_tasks += 1
      if task.rec_type == "MapAttempt":
        self.total_map_tasks += 1
      if task.rec_type == "ReduceAttempt":
        self.total_red_tasks += 1

      if not task.job_id in self.jobs:
        self.jobs[task.job_id] = Job(task.job_id)
      self.jobs[task.job_id].add_task(task)


      if get_server_list:
        if task.self_id not in self.servers:
          self.servers[task.self_id] = 1
          self.servers_list.append(task.self_id)

        # for other_id in task.other_ids:
        #   if other_id not in self.servers:
        #     self.servers[other_id] = 1
        #     self.servers_list.append(other_id)



    trace.close()

  def get_rand_server(self):
    return self.servers_list[random.randint(0, len(self.servers_list) - 1)]


def main(argv):
  u = Cluster()

if __name__ == "__main__":
  main(sys.argv[1:])


