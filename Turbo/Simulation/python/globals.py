
import heapq


global remaining_event_queue
global current_time

global flows_to_schedule
flows_to_schedule = []

remaining_event_queue = []
current_time = 0


capacity = 10000000000.0 # In bps
pd = 0.0000002 # propagation delay

#tx_time_packet = 1500 * 8 / capacity - pd


def add_to_event_queue(event):
  global remaining_event_queue
  heapq.heappush(remaining_event_queue, event)
  if event.time < current_time:
  	print "Something wrong"

def get_current_time():
  global current_time
  return current_time #in s

def get_next_event():
  global current_time
  global remaining_event_queue
  event = heapq.heappop(remaining_event_queue)
  """
  best = event_queue[0]
  best_index = 0
  for i in range(len(event_queue)):
  	if event_queue[i].time < best.time:
  		best = event_queue[i]
  		best_index = i
  event = event_queue.pop(i)
  """
  current_time = event.time
  return event