#include <iostream>
#include <fstream>
#include <assert.h>
#include <deque>
#include <float.h>
#include <algorithm>
#include <stdlib.h>
#include <vector>
#include <queue>
#include <sstream>


#define UNCREATED 1
#define CREATED 2
#define STARTED 3
#define SUSPENDED 4
#define FINISHED 5


#define FLOW_ARRIVAL 1
#define FLOW_FINISHED 2

uint32_t num_hosts = 144;

class IdealFlow;

class Event {
public:
  Event(uint32_t type, double time, IdealFlow *flow) {
    this->type = type;
    this->time = time;
    this->flow = flow;
    this->cancelled = false;
  }
  ~Event() {
  }
  bool operator == (const Event& e) const {
    return (time == e.time && type == e.type);
  }
  bool operator < (const Event& e) const {
    if (time < e.time) return true;
    else if (time == e.time && type < e.type) return true;
    else return false;
  }
  bool operator > (const Event& e) const {
    if (time > e.time) return true;
    else if (time == e.time && type > e.type) return true;
    else return false;
  }

  uint32_t type;
  double time;
  IdealFlow *flow;
  bool cancelled;
};

class FlowArrivalEvent : public Event {
public:
  FlowArrivalEvent(double time, IdealFlow *flow) : Event(FLOW_ARRIVAL, time, flow) {
  }
  ~FlowArrivalEvent();
};

class FlowFinishedEvent : public Event {
public:
  FlowFinishedEvent(double time, IdealFlow *flow) : Event(FLOW_FINISHED, time, flow) {
  }
  ~FlowFinishedEvent();
};

class IdealFlow {

public:
  IdealFlow(uint32_t id, double size, double start_time,
    uint32_t s, uint32_t d, double host_delay, double low_bw, bool cut_through);

  ~IdealFlow(); // Destructor

  double transmitted_size(double time);
  double remaining_time();

  uint32_t id;
  double size;
  double start_time;
  double finish_time;
  uint32_t s, d;
  double remaining_size;
  uint32_t state;
  double ideal_fct;
  double updated_time;
  double host_delay;
  uint32_t hop_count;
  double hop_delay;
  double low_bw;
  double high_bw;
  double oracle_fct;
  bool cut_through;
  FlowFinishedEvent *finish_event;
};

IdealFlow::IdealFlow(uint32_t id, double size, double start_time,
  uint32_t s, uint32_t d, double host_delay, double low_bw, bool cut_through) {
  this->id = id;
  this->size = size;
  this->start_time = start_time;
  this->s = s; this->d = d;
  this->remaining_size = size;
  this->state = UNCREATED;
  this->updated_time = 0;
  if (s / 16 == d / 16) {
    this->hop_count = 2;
  } else {
    this->hop_count = 4;
  }
  this->low_bw = low_bw;
  this->high_bw = 4 * low_bw;
  this->host_delay = host_delay;
  this->hop_delay = 0.2;
  this->cut_through = cut_through;


  this->oracle_fct = remaining_time();
}

double IdealFlow::transmitted_size(double time) {
  double elapsed_time = time - updated_time;
  if (elapsed_time < 0) {
    std::cout << " Time: " << time << " up: " << updated_time;
    assert(false);
  }
  return elapsed_time * low_bw;
}

double IdealFlow::remaining_time() {
  double pd = 4 * host_delay + 2 * hop_count * hop_delay;
  double td = 0;
  if (cut_through) {
    td = (remaining_size + 40.0 * 8) / low_bw;
    if (hop_count == 4) {
      td += 2*40.0*8.0/high_bw;
    }
  } else {
    td = (remaining_size + 1460.0*8) / low_bw;
    if (hop_count == 4) {
      td += 2*1460.0*8.0/high_bw;
    }
  }
  return pd + td;
}

struct EventComparator
{
    bool operator() (Event *a, Event *b) { return a->time > b->time; }
};

struct FlowComparator
{
    bool operator() (IdealFlow *a, IdealFlow *b) { return a->size < b->size; }
} fc;

uint32_t num_flows = 10;
IdealFlow **flows;
std::priority_queue<Event *, std::vector<Event *>, EventComparator> event_queue;
//std::priority_queue<IdealFlow *, std::vector<IdealFlow *>, FlowComparator> waiting_flows;
std::priority_queue<Event *, std::vector<Event *>, EventComparator> outstanding_events;
std::vector<IdealFlow *> waiting_flows;
int *ibusy;
int *ebusy;
uint32_t num_finished = 0;


void read_flows_to_schedule(std::string filename, double host_delay,
                            double low_bw, bool cut_through) {
  std::ifstream input(filename);
  std::string a;
  for (uint32_t i = 0; i < 10; i++) {
    std::getline(input, a);
    //std::cout << a;
    if (a.find("Running") != std::string::npos) {
      //char st[20];
      sscanf(a.c_str(), "%*s %d %*s", &num_flows);
    }
  }
  std::cout << "NUMBER OF FLOWS: " << num_flows << "\n";

  flows = new IdealFlow*[num_flows];
  for (uint32_t i = 0; i < num_flows; i++) {
    std::getline(input, a);
    std::stringstream ss(a);
    uint32_t id, s, d;
    double start_time;
    uint32_t size;
    ss >> id;
    ss >> size;
    ss >> s ; ss >> d;
    ss >> start_time;
    size = size * 8; // Convert to bits

    //std::cout << id << " " << start_time << " " << size << " "
    // << s << " " << d << "\n";
    flows[id] = new IdealFlow(id, size, start_time, s, d,
                              host_delay, low_bw, cut_through);
  }

  input.close();
}


void suspend(IdealFlow *f, double time) {
  if (f != NULL) {
    if (f->state != SUSPENDED) {
      f->remaining_size -= f->transmitted_size(time);
      f->updated_time = time;
      f->state = SUSPENDED;
      ibusy[f->s] = -1;
      ebusy[f->d] = -1;
      if(f->finish_event->unique_id == 5230)
        std::cout << "ideal.cpp:218 canceling 5230\n";
      f->finish_event->cancelled = true;
      waiting_flows.push_back(f);
    }
  }
}


void schedule(double time) {
  std::vector<IdealFlow *> waiting_flows_copy = waiting_flows;
  std::sort(waiting_flows_copy.begin(), waiting_flows_copy.end(), fc);
  waiting_flows.clear();

  for (uint32_t i = 0; i < waiting_flows_copy.size(); i++) {
    IdealFlow *f = waiting_flows_copy[i];
    uint32_t id = f->id;
    uint32_t iport = f->s;
    uint32_t eport = f->d;
    bool run = false;
    if (!(f->state == CREATED || f->state == SUSPENDED)) {
      assert (false);
    }
    if (ibusy[iport] == -1 && ebusy[eport] == -1) {
      run = true;
    } else {
      IdealFlow *flow1 = NULL;
      IdealFlow *flow2 = NULL;
      double r1 = DBL_MAX, r2 = DBL_MAX;
      if (ibusy[iport] != -1) {
        flow1 = flows[ibusy[iport]];
        r1 = flow1->remaining_size;
      }
      if (ebusy[eport] != -1) {
        flow2 = flows[ebusy[eport]];
        r2 = flow2->remaining_size;
      }
      double r = f->remaining_size;
      if (r < r1 && r < r2) {
        run = true;
        //if (flow1->id == 3 || flow2->id == 3)
        //std::cout << "Trying to suspend " << ibusy[iport] << " " << ebusy[eport] << std::endl;
        suspend(flow1, time);
        suspend(flow2, time);
      }
    }
    if (run) {
      ibusy[iport] = id;
      ebusy[eport] = id;
      //std::cout << "Setting suspended to " << id << std::endl;
      double d = f->remaining_time();
      double finish_time = time + d;
      f->state = STARTED;
      f->updated_time = time;
      //std::cout << "Setting finished_event for " << f->id << std::endl;
      f->finish_event = new FlowFinishedEvent(finish_time, f);
      event_queue.push(f->finish_event);
      //std::cout << "Scheduled flow id " << f->id << " to finish " << finish_time << std::endl;
    } else {
      waiting_flows.push_back(f);
    }
  }
}


void get_ideal_fcts(std::string filename, double host_delay, double low_bw,
                    bool cut_through) {
  read_flows_to_schedule(filename, host_delay, low_bw, cut_through);

  for (uint32_t i = 0; i < num_flows; i++) {
    IdealFlow *f = flows[i];
    outstanding_events.push(new FlowArrivalEvent(f->start_time, f));
  }
  ibusy = new int[num_hosts];
  ebusy = new int[num_hosts];
  for (uint32_t i = 0; i < num_hosts; i++) {
    ibusy[i] = -1;
    ebusy[i] = -1;
  }

  double time = 0;
  event_queue.push(outstanding_events.top());
  outstanding_events.pop();
  while (event_queue.size() > 0) {

    Event *ev = event_queue.top();
    event_queue.pop();
    IdealFlow *flow = ev->flow;
    time = ev->time;
    //std::cout << "Time updated to " << time << " NS " << num_finished << std::endl;

    if (ev->cancelled) {
      continue;
    }

    if (ev->type == FLOW_ARRIVAL) {
      //std::cout << "Here " << std::endl;
      flow->state = CREATED;
      flow->updated_time = ev->time;
      waiting_flows.push_back(flow);
      if (outstanding_events.size() > 0) {
        event_queue.push(outstanding_events.top());
        outstanding_events.pop();
      }
    } else if (ev->type == FLOW_FINISHED) {
      if (ibusy[flow->s] != flow->id || ebusy[flow->d] != flow->id) {
        std::cout << flow->id << " " << " but i: " << ibusy[flow->s]
          << " e: " << ebusy[flow->d] << "\n";
        assert(false);
      }
      ibusy[flow->s] = -1;
      ebusy[flow->d] = -1;
      flow->state = FINISHED;
      flow->finish_time = ev->time;
      flow->ideal_fct = flow->finish_time - flow->start_time;
      flow->updated_time = ev->time;
      num_finished += 1;
      if (num_finished % 1000 == 0) {
        std::cerr << "Finished " << num_finished << std::endl;
      }
    }
    schedule(time);
    //std::cout << "NF: " << num_finished << " s: " << event_queue.size() << std::endl;
  }

}


int main (int argc, char **argv) {
  std::cout.precision(15);
  if (argc < 5) {
    std::cerr << "Usage: ./ideal filename host_delay cut_through bandwidth\n";
    exit(0);
  }
  double host_delay = atof(argv[2]);
  bool cut_through = false;
  if (atoi(argv[3]) == 1) {
    cut_through = true;
  }
  double bw = 1000 * atof(argv[4]);
  get_ideal_fcts(std::string(argv[1]), host_delay, bw, cut_through);

  std::cout << "Lambda ideal\n";
  std::cout << "Running " << num_flows << " Flows\n";
  std::cout << "CDF_File ideal\n";
  std::cout << "Bandwidth " << 1000000.0 * bw << "\n";
  std::cout << "QueueSize ideal\n";
  std::cout << "CutThrough " << cut_through << "\n";
  std::cout << "FlowType ideal\n";
  std::cout << "QueueType ideal\n";
  std::cout << "Init CWND ideal\n";
  std::cout << "Max CWND ideal\n";
  std::cout << "Rtx Timeout ideal\n";
  double fct = 0;
  double norm = 0;
  for (uint32_t i = 0; i < num_flows; i++) {
    fct += flows[i]->ideal_fct;
    norm += (flows[i]->ideal_fct / flows[i]->oracle_fct);
    IdealFlow *f = flows[i];
    std::cout << f->id << " " << f->size / 8 << " " << f->s << " " << f->d <<
      " " << f->start_time << " " << f->finish_time << " " << f->ideal_fct <<
      " " << f->oracle_fct << " " << f->ideal_fct / f->oracle_fct << "\n";
  }
  std::cout << "AverageFCT " << fct / num_flows << " MeanSlowdown " <<
    norm / num_flows << std::endl;
  std::cout << "DeadPackets 0\n";
  return 0;
}
