from task import *

class Job:
  def __init__(self, id):
    self.job_id = id
    self.map_tasks = {}
    self.reduce_tasks = {}
    self.tasks = {}
    self.start_time = 0


  def add_task(self, task):
    if self.start_time == 0 or (task.start_time != 0 and task.start_time < self.start_time):
      self.start_time = task.start_time

    self.tasks[task.task_attempt_id] = task

    if task.rec_type == "MapAttempt":
      self.map_tasks[task.task_attempt_id] = task
    elif task.rec_type == "ReduceAttempt":
      self.reduce_tasks[task.task_attempt_id] = task

    task.job = self

