#include "experiment.h"

Experiment::Experiment() {}
Experiment::~Experiment() {}

void Experiment::read_experiment_parameters(
  std::string conf_filename,
  uint32_t exp_type
) {
  std::ifstream input(conf_filename);

  std::string temp;
  input >> temp; input >> this->params.initial_cwnd;
  input >> temp; input >> this->params.max_cwnd;
  input >> temp; input >> this->params.retx_timeout_value;
  input >> temp; input >> this->params.queue_size;
  input >> temp; input >> this->params.propagation_delay;
  input >> temp; input >> this->params.bandwidth;
  input >> temp; input >> this->params.queue_type;
  input >> temp; input >> this->params.flow_type;

  input >> temp;

  if (exp_type == DC_EXP_CONTINUOUS_FLOWMODEL) {
    input >> this->params.end_time;
  }
  else {
    input >> this->params.num_flows_to_run;
  }
  input >> temp; input >> this->params.cdf_or_flow_trace;
  input >> temp; input >> this->params.cut_through;
  input >> temp; input >> this->params.mean_flow_size;

  this->params.hdr_size = 40;
  this->params.mss = 1460;
}

void Experiment::add_to_event_queue(Event *ev) {
  event_queue.push(ev);
}

int Experiment::get_event_queue_size() {
  return event_queue.size();
}

double Experiment::get_current_time() {
  return current_time; // in us
}

/* Runs a initialized scenario */
void Experiment::run_scenario() {
  // Flow Arrivals create new flow arrivals
  // Add the first flow arrival
  if (this->flow_arrivals.size() > 0) {
    add_to_event_queue(this->flow_arrivals.front());
    this->flow_arrivals.pop_front();
  }
  while (this->event_queue.size() > 0) {
    Event *ev = this->event_queue.top();
    this->event_queue.pop();
    this->current_time = ev->time;
    if (this->start_time < 0) {
      this->start_time = this->current_time;
    }
    //event_queue.pop();
    //std::cout << get_current_time() << " Processing " << ev->type << " " << event_queue.size() << std::endl;
    if (ev->cancelled) {
      delete ev; //TODO: Smarter
      continue;
    }
    ev->process_event();
    delete ev;
  }
}


void PFabricExperiment::read_flows_to_schedule(
  std::string filename,
  uint32_t num_lines,
  PFabricTopology *topo
) {
  std::ifstream input(filename);
  for (uint32_t i = 0; i < num_lines; i++) {
    double start_time, temp;
    uint32_t size, s, d;
    uint32_t id;
    input >> id;
    input >> start_time;
    input >> temp;
    input >> temp; size = (uint32_t) (this->params.mss * temp);
    input >> temp; input >> temp;
    input >> s >> d;

    std::cout << "Flow " << id << " " << start_time << " " << size << " " << s << " " << d << "\n";
    this->flows_to_schedule.push_back(
      Factory::get_flow(
        id,
        start_time,
        size,
        topo->hosts[s],
        topo->hosts[d],
        this->params.flow_type
      )
    );
  }
  input.close();
}

void PFabricExperiment::generate_flows_to_schedule(
  std::string filename,
  uint32_t num_flows,
  PFabricTopology *topo
) {
  //double lambda = 4.0966649051007566;
  double lambda = params.bandwidth * 0.8 /
  (params.mean_flow_size * 8.0 / 1460 * 1500);
  double lambda_per_host = lambda / (topo->hosts.size() - 1);
  std::cout << "Lambda: " << lambda_per_host << std::endl;

  EmpiricalRandomVariable *nv_bytes =
  new EmpiricalRandomVariable(filename);
  ExponentialRandomVariable *nv_intarr =
  new ExponentialRandomVariable(1.0 / lambda_per_host);
  //* [expr ($link_rate*$load*1000000000)/($meanFlowSize*8.0/1460*1500)]
  for (uint32_t i = 0; i < topo->hosts.size(); i++) {
    for (uint32_t j = 0; j < topo->hosts.size(); j++) {
      if (i != j) {
        double first_flow_time = 1.0 + nv_intarr->value();
        add_to_event_queue(
        new FlowCreationForInitializationEvent(first_flow_time,
        topo->hosts[i], topo->hosts[j],
        nv_bytes, nv_intarr));
      }
    }
  }
  while (event_queue.size() > 0) {
    Event *ev = event_queue.top();
    event_queue.pop();
    current_time = ev->time;
    if (flows_to_schedule.size() < num_flows) {
      ev->process_event();
    }
    delete ev;
  }
  current_time = 0;
}

void PFabricExperiment::printQueueStatistics(PFabricTopology *topo) {
  double totalSentFromHosts = 0;
  for (std::vector<Host*>::iterator h = (topo->hosts).begin(); h != (topo->hosts).end(); h++) {
    totalSentFromHosts += (*h)->queue->b_departures;
  }

  double totalSentToHosts = 0;
  for (std::vector<AggSwitch*>::iterator tor = (topo->agg_switches).begin(); tor != (topo->agg_switches).end(); tor++) {
    std::vector<Queue*> host_facing_queues;
    for (std::vector<Queue*>::iterator q = ((*tor)->queues).begin(); q != ((*tor)->queues).end(); q++) {
      if ((*q)->rate == params.bandwidth) host_facing_queues.push_back((*q));
    }
    for (std::vector<Queue*>::iterator q = host_facing_queues.begin(); q!=host_facing_queues.end();q++) {
      totalSentToHosts += (*q)->b_departures;
    }
  }

  double dead_bytes = totalSentFromHosts - totalSentToHosts;
  double total_bytes = 0;
  for (std::deque<Flow*>::iterator f = flows_to_schedule.begin(); f != flows_to_schedule.end(); f++) {
    total_bytes += (*f)->size;
  }

  double simulation_time = current_time - start_time;
  double utilization = (totalSentFromHosts * 8.0 / 144.0) / simulation_time;

  std::cout
    << "DeadPackets "
    << 100.0 * (dead_bytes/total_bytes)
    << "% DuplicatedPackets "
    << 100.0 * duplicated_packets_received * 1460.0 / total_bytes
    << "% Utilization "
    << utilization / 1000000000 << "%\n";
}

void PFabricExperiment::run_experiment(
  int argc,
  char **argv,
  uint32_t exp_type
) {
  if (argc < 3) {
    std::cout << "Usage: <exe> exp_type conf_file" << std::endl;
    return;
  }
  std::string conf_filename(argv[2]);
  read_experiment_parameters(conf_filename, exp_type);
  params.num_hosts = 144;
  params.num_agg_switches = 9;
  params.num_core_switches = 4;


  if (params.cut_through == 1) {
    topology = new CutThroughTopology(params.num_hosts, params.num_agg_switches,
    params.num_core_switches, params.bandwidth, params.queue_type);
  } else {
    topology = new PFabricTopology(params.num_hosts, params.num_agg_switches,
    params.num_core_switches, params.bandwidth, params.queue_type);
  }


  PFabricTopology *topo = (PFabricTopology *) topology;

  uint32_t num_flows = params.num_flows_to_run;
  if (exp_type == DC_EXP_WITH_TRACE) {
    this->read_flows_to_schedule(params.cdf_or_flow_trace, num_flows, topo);
  } else if (exp_type == DC_EXP_WITHOUT_TRACE) {
    this->generate_flows_to_schedule(params.cdf_or_flow_trace, num_flows, topo);
  }
  std::deque<Flow *> flows_sorted = flows_to_schedule;
  struct FlowComparator {
    bool operator() (Flow *a, Flow *b) {
      return a->start_time < b->start_time;
    }
  } fc;
  std::sort (flows_sorted.begin(), flows_sorted.end(), fc);

  for(uint32_t i = 0; i < flows_sorted.size(); i++) {
    Flow *f = flows_sorted[i];
    flow_arrivals.push_back(new FlowArrivalEvent(f->start_time, f));
  }

  add_to_event_queue(new LoggingEvent((flows_sorted.front())->start_time + 0.01));

  std::cout << "Running " << num_flows << " Flows\nCDF_File " <<
  params.cdf_or_flow_trace << "\nBandwidth " << params.bandwidth/1e9 <<
  "\nQueueSize " << params.queue_size <<
  "\nCutThrough " << params.cut_through <<
  "\nFlowType " << params.flow_type <<
  "\nQueueType " << params.queue_type <<
  "\nInit CWND " << params.initial_cwnd <<
  "\nMax CWND " << params.max_cwnd <<
  "\nRtx Timeout " << params.retx_timeout_value << std::endl;

  run_scenario();
  // print statistics
  double sum = 0, sum_norm = 0;
  for (uint32_t i = 0; i < flows_sorted.size(); i++) {
    Flow *f = flows_to_schedule[i];
    sum += 1000000.0 * f->flow_completion_time;
    sum_norm += 1000000.0 * f->flow_completion_time /
    topology->get_oracle_fct(f);
  }
  std::cout << "AverageFCT " << sum / flows_sorted.size() <<
  " MeanSlowdown " << sum_norm / flows_sorted.size() << "\n";
  printQueueStatistics(topo);
}


void ContinuousModelExperiment::generate_flows_to_schedule(
  std::string filename,
  uint32_t num_flows,
  PFabricTopology *topo
) {
  //double lambda = 4.0966649051007566;
  double lambda = params.bandwidth * 0.8 /
  (params.mean_flow_size * 8.0 / 1460 * 1500);
  double lambda_per_host = lambda / (topo->hosts.size() - 1);
  std::cout << "Lambda: " << lambda_per_host << std::endl;

  EmpiricalRandomVariable *nv_bytes =
  new EmpiricalRandomVariable(filename);
  ExponentialRandomVariable *nv_intarr =
  new ExponentialRandomVariable(1.0 / lambda_per_host);

  //* [expr ($link_rate*$load*1000000000)/($meanFlowSize*8.0/1460*1500)]
  // schedule the first flow between each pair of hosts
  for (uint32_t i = 0; i < topo->hosts.size(); i++) {
    for (uint32_t j = 0; j < topo->hosts.size(); j++) {
      if (i != j) {
        double first_flow_time = 1.0 + nv_intarr->value();
        add_to_event_queue(
          new FlowCreationForInitializationEventWithTimeLimit(
            end_time,
            first_flow_time,
            topo->hosts[i],
            topo->hosts[j],
            nv_bytes,
            nv_intarr
          )
        );
      }
    }
  }

  // process the flow creation events, which add any additional flows
  while (event_queue.size() > 0) {
    Event *ev = event_queue.top();
    event_queue.pop();
    current_time = ev->time;
    if (current_time < end_time) {
      ev->process_event();
    }
    delete ev;
  }
  current_time = 0;
}

void ContinuousModelExperiment::run_experiment(
  int argc,
  char **argv,
  uint32_t exp_type
) {
  if (argc < 3) {
    std::cout << "Usage: <exe> exp_type conf_file" << std::endl;
    return;
  }
  std::string conf_filename(argv[2]);
  read_experiment_parameters(conf_filename, DC_EXP_CONTINUOUS_FLOWMODEL);
  params.num_hosts = 144;
  params.num_agg_switches = 9;
  params.num_core_switches = 4;


  if (params.cut_through == 1) {
    topology = new CutThroughTopology(params.num_hosts, params.num_agg_switches,
    params.num_core_switches, params.bandwidth, params.queue_type);
  } else {
    topology = new PFabricTopology(params.num_hosts, params.num_agg_switches,
    params.num_core_switches, params.bandwidth, params.queue_type);
  }

  PFabricTopology *topo = (PFabricTopology *) topology;

  //use the num_flows parameter for the end time.
  this->end_time = params.end_time;
  std::cout << "end time: " << end_time << std::endl;
  //generation only for continuous model. no read from trace.
  generate_flows_to_schedule(params.cdf_or_flow_trace, end_time, topo);
  std::deque<Flow *> flows_sorted = flows_to_schedule;
  struct FlowComparator {
    bool operator() (Flow *a, Flow *b) {
      return a->start_time < b->start_time;
    }
  } fc;
  std::sort (flows_sorted.begin(), flows_sorted.end(), fc);

  for(uint32_t i = 0; i < flows_sorted.size(); i++) {
    Flow *f = flows_sorted[i];
    flow_arrivals.push_back(new FlowArrivalEvent(f->start_time, f));
  }

  add_to_event_queue(new LoggingEvent((flows_sorted.front())->start_time + 0.01));

  std::cout
  << "Running Until time " << end_time
  << "\nCDF_File " << params.cdf_or_flow_trace
  << "\nBandwidth " << params.bandwidth/1e9
  << "\nQueueSize " << params.queue_size
  << "\nCutThrough " << params.cut_through
  << "\nFlowType " << params.flow_type
  << "\nQueueType " << params.queue_type
  << "\nInit CWND " << params.initial_cwnd
  << "\nMax CWND " << params.max_cwnd
  << "\nRtx Timeout " << params.retx_timeout_value
  << std::endl;

  this->run_scenario();
  // print statistics
  double sum = 0, sum_norm = 0;
  uint32_t num_finished_flows = 0;
  double unfinished_flows_size = 0;
  for (uint32_t i = 0; i < flows_sorted.size(); i++) {
    Flow *f = flows_sorted[i];
    if (f->finished != 0) {
      num_finished_flows ++;
      sum += 1000000.0 * f->flow_completion_time;
      sum_norm += 1000000.0 * f->flow_completion_time /
      topology->get_oracle_fct(f);
    }
    else {
      std::cout
        << "Unfinished "
        << f->id << " "
        << f->size << " "
        << f->src->id << " "
        << f->dst->id << " "
        << f->start_time << " "
        << std::endl;
      unfinished_flows_size += f->size;
    }
  }
  uint32_t num_unfinished_flows = flows_sorted.size() - num_finished_flows;
  std::cout
    << "AverageFCT " << sum / num_finished_flows
    << " MeanSlowdown " << sum_norm / num_finished_flows
    << std::endl;
  std::cout
    << "Num Unfinished Flows " << num_unfinished_flows
    << " Average Unifinished Flow Size " << unfinished_flows_size / num_unfinished_flows
    << std::endl;
  printQueueStatistics(topo);
}

void ContinuousModelExperiment::run_scenario() {
  // Flow Arrivals create new flow arrivals
  // Add the first flow arrival
  if (flow_arrivals.size() > 0) {
    add_to_event_queue(flow_arrivals.front());
    flow_arrivals.pop_front();
  }
  while (event_queue.size() > 0) {
    Event *ev = event_queue.top();
    if (ev->time > end_time) {
      //stop the experiment
      break;
    }
    event_queue.pop();
    current_time = ev->time;
    if (start_time < 0) {
      start_time = current_time;
    }
    //event_queue.pop();    //std::cout << get_current_time() << " Processing " << ev->type << " " << event_queue.size() << std::endl;
    if (ev->cancelled) {
      delete ev; //TODO: Smarter
      continue;
    }
    ev->process_event();
    delete ev;
  }
}


void FixedDistributionExperiment::generate_flows_to_schedule(
  std::string filename,
  uint32_t num_flows,
  PFabricTopology *topo
) {
  //double lambda = 4.0966649051007566;
  double lambda = params.bandwidth * 0.8 /
  (params.mean_flow_size * 8.0 / 1460 * 1500);
  double lambda_per_host = lambda / (topo->hosts.size() - 1);
  std::cout << "Lambda: " << lambda_per_host << std::endl;

  //use an NAryRandomVariable for true uniform/bimodal/trimodal/etc
  EmpiricalRandomVariable *nv_bytes =
    new NAryRandomVariable(filename);
  ExponentialRandomVariable *nv_intarr =
    new ExponentialRandomVariable(1.0 / lambda_per_host);
  //* [expr ($link_rate*$load*1000000000)/($meanFlowSize*8.0/1460*1500)]
  for (uint32_t i = 0; i < topo->hosts.size(); i++) {
    for (uint32_t j = 0; j < topo->hosts.size(); j++) {
      if (i != j) {
        double first_flow_time = 1.0 + nv_intarr->value();
        add_to_event_queue(
        new FlowCreationForInitializationEvent(first_flow_time,
        topo->hosts[i], topo->hosts[j],
        nv_bytes, nv_intarr));
      }
    }
  }
  while (event_queue.size() > 0) {
    Event *ev = event_queue.top();
    event_queue.pop();
    current_time = ev->time;
    if (flows_to_schedule.size() < num_flows) {
      ev->process_event();
    }
    delete ev;
  }
  current_time = 0;
}
