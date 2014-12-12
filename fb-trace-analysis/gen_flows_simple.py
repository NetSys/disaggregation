from cluster import *
from lib import *
import random
import math
import sys





class FlowContainer:
  def __init__(self):
    self.flow_size_count = {}
    self.flow_size_in_packet_count = {}
    self.flow_count = 0
    self.name_dict = {"file_read":0,
               "file_written":1,
               "Map_file_write":2,
               "Reduce_file_read":3,
               "Map_CPU_Mem_read":4,
               "Map_CPU_Mem_write":5,
               "Reduce_CPU_Mem_read":4,
               "Reduce_CPU_Mem_write":5,
               "hdfs_read_local": 6,
               "hdfs_read_remote":7,
               "hdfs_written_local": 8,
               "hdfs_written_remote":9,
               "Shuffle":10
               }




def get_map_read(input_bytes):
  if input_bytes < 1024 * 1024 * 1024:
    return 0
  r = input_bytes * 1.83188930e-03 + 7.78490125e+06
  return max(r,0)#, 100 * 1024*1024)

def get_map_write(input_bytes):
  if input_bytes < 1024 * 1024 * 1024:
    return 0
  r = input_bytes * 2.44301455e-03 + 9.48375082e+06
  return max(r,0)

def get_reduce_read(input_bytes):
  r = input_bytes * 2.59458115e-02 + -1.19961465e+06
  return max(r,0)

def get_reduce_write(input_bytes):
  r = input_bytes * 8.42096985e-02 + -6.98675589e+06
  return max(r,0)

def gen_flows_simple(u, d_disk, d_mem, hdfs_block_size_mb = 1):
  print "gen_flows Version:", 23, "d_disk:", d_disk, "d_mem:", d_mem, "blk_sz:", hdfs_block_size_mb

  hdfs_block_size_mb_old = 128
  hdfs_block_size = int(1024*1024*hdfs_block_size_mb)
  hdfs_block_size_old = int(1024*1024*hdfs_block_size_mb_old)
  mem_page_size = 4096
  percent_local_read = 0.9


  next_percent = 0.01
  count = 0
  container = FlowContainer()
  for job in u.jobs.itervalues():
    #if len(job.reduce_tasks) < 2 and len(job.map_tasks) < 2:
    #  continue
    for task in job.tasks.itervalues():
      count += 1
      if task.map_input_bytes > 1 * 1024 * 1024 * 1024 or task.reduce_shuffle_bytes > 1 * 1024 * 1024 * 1024:
        continue
      if float(count)/u.total_tasks > next_percent:
        print "Finished", next_percent, "(", count, "/", u.total_tasks, ") Flows added:", container.flow_count
        next_percent += 0.01

      # if len(job.map_tasks) == 0 or len(job.reduce_tasks) == 0:
      #   if task.file_bytes_read > 0:
      #     if d_disk:
      #       num_of_blocks = task.file_bytes_read/hdfs_block_size + 1
      #       for i in range(0, num_of_blocks):
      #         if i == num_of_blocks -1:
      #           read_size = task.file_bytes_read%hdfs_block_size
      #         else:
      #           read_size = hdfs_block_size
      #         record = Flow_record(task.start_time, task.self_id + "_disk", task.self_id + "_mem", read_size, "file_read")
      #         add_flow(record, container)
      #     else:
      #       pass # no network traffic is generated
      #
      #   if task.file_bytes_written > 0:
      #     if d_disk:
      #       num_of_blocks = task.file_bytes_written/hdfs_block_size + 1
      #       for i in range(0, num_of_blocks):
      #         if i == num_of_blocks-1:
      #            write_size = task.file_bytes_written%hdfs_block_size
      #         else:
      #            write_size = hdfs_block_size
      #         record = Flow_record(task.start_time + task.cpu_ms, task.self_id + "_mem", task.self_id + "_disk", write_size, "file_written")
      #         add_flow(record, container)
      #     else:
      #       pass # no network traffic is generated


      #shuffle traffic
      if len(job.map_tasks) > 0 and len(job.reduce_tasks) > 0:
        if task.rec_type == "ReduceAttempt" and task.reduce_shuffle_bytes > 0:
          reduce_flow_size = task.reduce_shuffle_bytes / len(job.map_tasks)
          if d_disk:
            add_flow(hdfs_block_size, "Map_file_write", (reduce_flow_size / hdfs_block_size) * len(job.map_tasks), container)
            add_flow(hdfs_block_size, "Reduce_file_read", (reduce_flow_size / hdfs_block_size) * len(job.map_tasks), container)
            add_flow(reduce_flow_size % hdfs_block_size, "Map_file_write", len(job.map_tasks), container)
            add_flow(hdfs_block_size % hdfs_block_size, "Reduce_file_read", len(job.map_tasks), container)
          else:
            add_flow(reduce_flow_size, "Shuffle", len(job.map_tasks), container)




      #Map memory access
      if task.map_input_bytes > 0:
        if d_mem:
          map_read = int(get_map_read(task.map_input_bytes))
          map_write = int(get_map_write(task.map_input_bytes))
          cpu_ram_read_blocks = map_read / mem_page_size
          cpu_ram_write_blocks = map_write / mem_page_size
          add_flow(mem_page_size, "Map_CPU_Mem_read", cpu_ram_read_blocks, container)
          add_flow(mem_page_size, "Map_CPU_Mem_write", cpu_ram_write_blocks, container)
          add_flow(map_read % mem_page_size, "Map_CPU_Mem_read", 1, container)
          add_flow(map_write % mem_page_size, "Map_CPU_Mem_write", 1, container)
        else:
          pass #no network traffic

      #reduce memory access
      if task.reduce_shuffle_bytes > 0:
        if d_mem:
          red_read = int(get_reduce_read(task.reduce_shuffle_bytes))
          red_write = int(get_reduce_write(task.reduce_shuffle_bytes))
          cpu_ram_read_blocks = red_read / mem_page_size
          cpu_ram_write_blocks = red_write / mem_page_size
          add_flow(mem_page_size, "Reduce_CPU_Mem_read", cpu_ram_read_blocks, container)
          add_flow(mem_page_size, "Reduce_CPU_Mem_write", cpu_ram_write_blocks, container)
          add_flow(cpu_ram_read_blocks % mem_page_size, "Reduce_CPU_Mem_read", 1, container)
          add_flow(cpu_ram_write_blocks % mem_page_size, "Reduce_CPU_Mem_write", 1, container)
        else:
          pass #no network traffic







      if task.hdfs_bytes_read > 0:
        if d_disk:
          num_blocks = task.hdfs_bytes_read/hdfs_block_size
          add_flow(hdfs_block_size, "hdfs_read_remote", num_blocks, container)
          add_flow(task.hdfs_bytes_read % hdfs_block_size, "hdfs_read_remote", 1, container)
        else:
          num_blocks = task.hdfs_bytes_read/hdfs_block_size_old+1
          local_read = int(num_blocks * percent_local_read)
          remote_read = num_blocks - local_read
          add_flow(hdfs_block_size_old, "hdfs_read_local", local_read, container)
          add_flow(hdfs_block_size_old, "hdfs_read_remote", remote_read, container)


      if task.hdfs_bytes_written > 0:
        if d_disk:
          num_blocks = task.hdfs_bytes_written/hdfs_block_size
          add_flow(hdfs_block_size, "hdfs_written_remote", num_blocks * 3, container)
          add_flow(hdfs_block_size, "hdfs_written_remote", num_blocks * 3, container)
          add_flow(task.hdfs_bytes_written%hdfs_block_size, "hdfs_written_remote", 3, container)
          add_flow(task.hdfs_bytes_written%hdfs_block_size, "hdfs_written_remote", 3, container)
        else:
          num_blocks = task.hdfs_bytes_written/hdfs_block_size_old
          add_flow(hdfs_block_size_old, "hdfs_written_local", num_blocks, container)
          add_flow(hdfs_block_size_old, "hdfs_written_remote", num_blocks*2, container)
          add_flow(task.hdfs_bytes_written%hdfs_block_size_old, "hdfs_written_local", 1, container)
          add_flow(task.hdfs_bytes_written%hdfs_block_size_old, "hdfs_written_remote", 2, container)



  print "Finished sorting"

  if d_disk:
    d_label = "d"
  else:
    d_label = ""

  if d_mem:
    m_label = "m"
  else:
    m_label = ""

  print "in byte:"
  flow_detail_dist_file = open("results/" + u.name + "_" + str(hdfs_block_size_mb) + "_detail_dist_" + d_label + m_label + ".txt2", "w")
  for fsize in sorted(container.flow_size_count):
    detail_line_to_write = str(fsize) + " " + " ".join(map(str, container.flow_size_count[fsize]))
    print detail_line_to_write
    flow_detail_dist_file.write(detail_line_to_write + "\n")
  flow_detail_dist_file.close()

  print "in pkt:"
  flow_dist_in_packet_file = open("results/" + u.name + "_" + str(hdfs_block_size_mb) + "_dist_in_packet_" + d_label + m_label + ".txt2", "w")
  for fsize in sorted(container.flow_size_in_packet_count):
    percent = reduce(lambda x,y: x + y, container.flow_size_in_packet_count[fsize])/float(container.flow_count)
    container.flow_size_in_packet_count[fsize].append(percent)
    sum_line_to_write = str(fsize) + "\t" + str(percent)
    print sum_line_to_write
    flow_dist_in_packet_file.write(sum_line_to_write + "\n")
  flow_dist_in_packet_file.close()

  return container.flow_size_in_packet_count





def add_flow(flow_size, rec_type, count, container):
  if flow_size <= 0:
    return
  container.flow_count += count

  flowSizeKey = int(round(pow(10,round(math.log10(flow_size),1)),0))

  if flowSizeKey not in container.flow_size_count:
    container.flow_size_count[flowSizeKey] = [0,0,0,0,0,0,0,0,0,0,0]
  container.flow_size_count[flowSizeKey][container.name_dict[rec_type]] += count



  num_pkts = int(flow_size/1460+1)
  base = int(math.pow(10, int(math.floor(math.log10(num_pkts)))))
  flowSizeInPktKey = num_pkts/base*base

  if flowSizeInPktKey not in container.flow_size_in_packet_count:
    container.flow_size_in_packet_count[flowSizeInPktKey] = [0,0,0,0,0,0,0,0,0,0,0]
  container.flow_size_in_packet_count[flowSizeInPktKey][container.name_dict[rec_type]] += count






def main(argv):

  # d_disk = False
  # if "-d" in argv:
  #   print "disaggregated disk mode"
  #   d_disk = True
  #
  # d_mem = False
  # if "-m" in argv:
  #   print "disaggregated mem mode"
  #   d_mem = True


  u = Cluster("../../ramdisk/24h.txt", get_server_list=False)


  o = gen_flows_simple(u, False, False, hdfs_block_size_mb = 1)
  d = gen_flows_simple(u, True, False, hdfs_block_size_mb = 1)
  dm = gen_flows_simple(u, True, True, hdfs_block_size_mb = 1)

  k_plus = 0
  for k in o:
    if k >= 1000:
      k_plus += o[k][-1]
  o[1000][-1] = k_plus

  print "summary"
  for key in range(1,10) + range(10,100,10) + range(100,1000,100) + [1000]:
    if key not in o:
      r_o = 0
    else:
      r_o = o[key][-1]
    if key not in d:
      r_d = 0
    else:
      r_d = d[key][-1]
    if key not in dm:
      r_dm = 0
    else:
      r_dm = dm[key][-1]
    print "\t".join([str(key), str(r_o), str(r_d), str(r_dm)])

if __name__ == "__main__" :
  main(sys.argv[1:])


