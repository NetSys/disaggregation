from lib import *

class Task:
  def __init__(self, line):
    self.line = line
    line_arr = line.split(" ")
    #self.job_id = line_arr[0].split("_")[1]
    #self.task_id = line_arr[0].split("_")[2]
    self.job_id = line_arr[0]
    self.rec_type = line_arr[1]
    self.task_attempt_id = line_arr[2]
    self.task_status = line_arr[3]
    self.start_time = self.get_int(line_arr[4])
    self.finish_time = self.get_int(line_arr[5])
    self.cpu_ms = self.get_int(line_arr[6])
    self.phys_mem_bytes = self.get_int(line_arr[7])
    self.virt_mem_bytes = self.get_int(line_arr[8])
    self.file_bytes_read = self.get_int(line_arr[9])
    self.file_bytes_written = self.get_int(line_arr[10])
    self.hdfs_bytes_read = self.get_int(line_arr[11])
    self.hdfs_bytes_written = self.get_int(line_arr[12])
    self.map_input_bytes = self.get_int(line_arr[13])
    self.reduce_shuffle_bytes = self.get_int(line_arr[14])
    self.spilled_records = self.get_int(line_arr[15])
    self.shuffle_finished = self.get_int(line_arr[16])
    self.sort_finished = self.get_int(line_arr[17])

    self.self_id = get_hadoop_id(line_arr[18])
    self.other_ids = []
    for entry in line_arr[19].split(","):
      hadoop_id = get_hadoop_id(entry)
      if not hadoop_id == "":
        self.other_ids.append(hadoop_id)


  def get_int(self, str):
    if str == "\N":
      return 0
    else:
      return int(str)

