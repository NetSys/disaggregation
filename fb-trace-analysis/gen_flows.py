from cluster import *
from lib import *
import random
import math
import sys




class Flow_record:
  count = 0
  write_records_to_file = True
  def __init__(self, time, from_id, to_id, size, rec_type):
    self.id = Flow_record.count
    Flow_record.count += 1
    self.time = time
    self.from_id = from_id
    self.to_id = to_id
    self.size = size
    self.rec_type = rec_type

  def __str__(self):
    return str(self.time) + "," + self.from_id + "," + self.to_id + "," + str(self.size) + "," + self.rec_type

  def to_ns2_str(self):
    return " ".join([str(self.id), str(self.time), "0", str(self.size), "0", "0", self.from_id, self.to_id])

  @classmethod
  def from_str(cls, record):
    entires = record.split(",")
    time = int(entires[0])
    from_id = entires[1]
    to_id = entires[2]
    size=int(entires[3])
    rec_type=entires[4]
    return Flow_record(time, from_id, to_id, size, rec_type)


class FlowContainer:
  def __init__(self):
    self.flows = []
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
               "hdfs_written_remote":9
               }




def get_map_read(input_bytes):
  if input_bytes < 1024 * 1024 * 1024:
    return 0
  r = input_bytes * 1.83188930e-03 + 7.78490125e+06
  return max(r,0)

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

def gen_flows(u, d_disk, d_mem, hdfs_block_size_mb = 1):
  print "gen_flows Version:", 20

  hdfs_block_size_mb_old = 128
  hdfs_block_size = int(1024*1024*hdfs_block_size_mb)
  hdfs_block_size_old = int(1024*1024*hdfs_block_size_mb_old)
  mem_page_size = 4096
  percent_local_read = 0.9

  #map_read_ratio = (391 * 1024 * 1024) / (4.5 * 1024 * 1024 * 1024)
  #map_write_ratio = (430 * 1024 * 1024) / (4.5 * 1024 * 1024 * 1024)

  #reduce_read_ratio = (100 * 1024 * 1024) / (2.8 * 1024 * 1024 * 1024)
  #reduce_write_ratio = (110 * 1024 * 1024) / (2.8 * 1024 * 1024 * 1024)


  next_percent = 0.01
  count = 0
  container = FlowContainer()
  for job in u.jobs.itervalues():
    for task in job.tasks.itervalues():
      count += 1
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
          for mapper in job.map_tasks.itervalues():
            if d_disk:
              num_of_blocks = int(reduce_flow_size / hdfs_block_size + 1)
              for i in range(0, num_of_blocks):
                if i == num_of_blocks - 1:
                  io_size = reduce_flow_size % hdfs_block_size
                else:
                  io_size = hdfs_block_size
                storage_node = u.get_rand_server()
                write_record = Flow_record(mapper.start_time + mapper.cpu_ms, mapper.self_id + "_cpu", storage_node + "_mem", io_size, "Map_file_write")
                read_record = Flow_record(task.start_time, storage_node + "_mem", task.self_id + "_cpu", io_size, "Reduce_file_read")
                add_flow(write_record, container)
                add_flow(read_record, container)
            else:
              record = Flow_record(mapper.start_time + mapper.cpu_ms, mapper.self_id + "_disk", task.self_id + "_disk", reduce_flow_size, "Map_file_write")
              add_flow(record, container)



      #Map memory access
      if task.map_input_bytes > 0:
        if d_mem:
          cpu_ram_read_blocks = int(get_map_read(task.map_input_bytes) / mem_page_size)
          cpu_ram_write_blocks = int( get_map_write(task.map_input_bytes) / mem_page_size)
          for i in range(0, cpu_ram_read_blocks):
            read_record = Flow_record(int(task.start_time + (task.finish_time - task.start_time) * float(i) / cpu_ram_read_blocks),
                                      task.self_id + "_mem",
                                      u.get_rand_server() + "_cpu",
                                      mem_page_size,
                                      "Map_CPU_Mem_read"
                                      )
            add_flow(read_record, container)


          for i in range(0, cpu_ram_write_blocks):
            write_record = Flow_record(int(task.start_time + (task.finish_time - task.start_time) * float(i) / cpu_ram_write_blocks),
                                      u.get_rand_server() + "_cpu",
                                      task.self_id + "_mem",
                                      mem_page_size,
                                      "Map_CPU_Mem_write"
                                      )
            add_flow(write_record, container)
        else:
          pass #no network traffic

      #reduce memory access
      if task.reduce_shuffle_bytes > 0:
        if d_mem:
          cpu_ram_read_blocks = int( get_reduce_read(task.reduce_shuffle_bytes) / mem_page_size)
          cpu_ram_write_blocks = int( get_reduce_write(task.reduce_shuffle_bytes) / mem_page_size)
          for i in range(0, cpu_ram_read_blocks):
            read_record = Flow_record(int(task.start_time + (task.finish_time - task.start_time) * float(i) / cpu_ram_read_blocks),
                                      task.self_id + "_mem",
                                      u.get_rand_server() + "_cpu",
                                      mem_page_size,
                                      "Reduce_CPU_Mem_read"
                                      )
            add_flow(read_record, container)

          for i in range(0, cpu_ram_write_blocks):
            write_record = Flow_record(int(task.start_time + (task.finish_time - task.start_time) * float(i) / cpu_ram_write_blocks),
                                      u.get_rand_server() + "_cpu",
                                      task.self_id + "_mem",
                                      mem_page_size,
                                      "Reduce_CPU_Mem_write"
                                      )
            add_flow(write_record, container)
        else:
          pass #no network traffic







      if task.hdfs_bytes_read > 0:
        if d_disk:
          num_blocks = task.hdfs_bytes_read/hdfs_block_size+1
          for i in range(0, num_blocks):
            if i == num_blocks - 1:
              read_size = task.hdfs_bytes_read%hdfs_block_size
            else:
              read_size = hdfs_block_size
            rec_type = "hdfs_read_remote"
            if len(task.other_ids) > 0:
              source = task.other_ids[i%len(task.other_ids)]
            else:
              source = u.get_rand_server()
            record = Flow_record(task.start_time, source + "_disk", task.self_id + "_mem", read_size, rec_type)
            add_flow(record, container)
        else:
          num_blocks = task.hdfs_bytes_read/hdfs_block_size_old+1
          for i in range(0, num_blocks):
            if i == num_blocks - 1:
              read_size = task.hdfs_bytes_read%hdfs_block_size_old
            else:
              read_size = hdfs_block_size_old
            if random.random() < percent_local_read:
              source = task.self_id
              rec_type = "hdfs_read_local"
            else:
              rec_type = "hdfs_read_remote"
              if len(task.other_ids) > 0:
                source = task.other_ids[i%len(task.other_ids)]
              else:
                source = u.get_rand_server()
            record = Flow_record(task.start_time, source + "_disk", task.self_id + "_mem", read_size, rec_type)
            add_flow(record, container)


      if task.hdfs_bytes_written > 0:
        if d_disk:
          num_blocks = task.hdfs_bytes_written/hdfs_block_size + 1
          for i in range(0, num_blocks):
            if i == num_blocks - 1:
              write_size = task.hdfs_bytes_written%hdfs_block_size
            else:
              write_size = hdfs_block_size
            if write_size > 0:
              record1 = Flow_record(task.start_time + task.cpu_ms, task.self_id + "_mem", task.self_id + "_disk", write_size, "hdfs_written_remote")
              record2 = Flow_record(task.start_time + task.cpu_ms, task.self_id + "_mem", u.get_rand_server() + "_disk", write_size, "hdfs_written_remote")
              record3 = Flow_record(task.start_time + task.cpu_ms, task.self_id + "_mem", u.get_rand_server() + "_disk", write_size, "hdfs_written_remote")
              add_flow(record1, container)
              add_flow(record2, container)
              add_flow(record3, container)
        else:
          num_blocks = task.hdfs_bytes_written/hdfs_block_size_old + 1
          for i in range(0, num_blocks):
            if i == num_blocks - 1:
              write_size = task.hdfs_bytes_written%hdfs_block_size_old
            else:
              write_size = hdfs_block_size_old
            if write_size > 0:
              record1 = Flow_record(task.start_time + task.cpu_ms, task.self_id + "_mem", task.self_id + "_disk", write_size, "hdfs_written_local")
              record2 = Flow_record(task.start_time + task.cpu_ms, task.self_id + "_mem", u.get_rand_server() + "_disk", write_size, "hdfs_written_remote")
              record3 = Flow_record(task.start_time + task.cpu_ms, task.self_id + "_mem", u.get_rand_server() + "_disk", write_size, "hdfs_written_remote")
              add_flow(record1, container)
              add_flow(record2, container)
              add_flow(record3, container)


  print "Start sorting. Total flows added:", len(container.flows)
  container.flows.sort(key=lambda r : r.time)

  print "Finished sorting"

  if d_disk:
    d_label = "d"
  else:
    d_label = ""

  if d_mem:
    m_label = "m"
  else:
    m_label = ""

  flow_detail_dist_file = open("results/" + u.name + "_" + str(hdfs_block_size_mb) + "_detail_dist_" + d_label + m_label + ".txt", "w")
  for fsize in sorted(container.flow_size_count):
    detail_line_to_write = str(fsize) + " " + " ".join(map(str, container.flow_size_count[fsize]))
    print detail_line_to_write
    flow_detail_dist_file.write(detail_line_to_write + "\n")
  flow_detail_dist_file.close()


  flow_dist_in_packet_file = open("results/" + u.name + "_" + str(hdfs_block_size_mb) + "_dist_in_packet_" + d_label + m_label + ".txt", "w")
  for fsize in sorted(container.flow_size_in_packet_count):
    sum_line_to_write = str(fsize) + " " + str(reduce(lambda x,y: x + y, container.flow_size_in_packet_count[fsize])/float(container.flow_count))
    flow_dist_in_packet_file.write(sum_line_to_write + "\n")
  flow_dist_in_packet_file.close()



  flow_file = open("../../ramdisk/" + u.name + "_" + str(hdfs_block_size_mb) +"_sortedflows.txt","w")
  for r in container.flows:
    flow_file.write(r.to_ns2_str() + "\n")
  flow_file.close()





def add_flow(flow, container):
  container.flow_count +=1
  if Flow_record.write_records_to_file:
    container.flows.append(flow)

  flowSizeKey = int(round(pow(10,round(math.log10(flow.size),1)),0))

  if flowSizeKey not in container.flow_size_count:
    container.flow_size_count[flowSizeKey] = [0,0,0,0,0,0,0,0,0,0]
  container.flow_size_count[flowSizeKey][container.name_dict[flow.rec_type]] += 1



  num_pkts = int(flow.size/1460+1)
  base = int(math.pow(10, int(math.floor(math.log10(num_pkts)))))
  flowSizeInPktKey = num_pkts/base*base

  if flowSizeInPktKey not in container.flow_size_in_packet_count:
    container.flow_size_in_packet_count[flowSizeInPktKey] = [0,0,0,0,0,0,0,0,0,0]
  container.flow_size_in_packet_count[flowSizeInPktKey][container.name_dict[flow.rec_type]] += 1






def main(argv):
  if "-s" in argv:
    print "No trace file will be produced"
    Flow_record.write_records_to_file = False
  else:
    print "A trade file will be produced"

  d_disk = False
  if "-d" in argv:
    print "disaggregated disk mode"
    d_disk = True

  d_mem = False
  if "-m" in argv:
    print "disaggregated mem mode"
    d_mem = True


  u = Cluster("../../ramdisk/1h.txt")


  gen_flows(u, d_disk, d_mem, hdfs_block_size_mb = 1)

if __name__ == "__main__" :
  main(sys.argv[1:])


