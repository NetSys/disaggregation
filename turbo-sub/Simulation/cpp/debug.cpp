#include "debug.h"
#include <set>

bool debug_mode = false;
bool print_flow = true;

bool debug_all_flows = false;
std::set<uint32_t> flows_to_debug_set = {91};
bool debug_all_queues = false;
std::set<uint32_t> queues_to_debug_set = {};
bool debug_all_hosts = false;
std::set<uint32_t> hosts_to_debug_set = {12};

bool debug_flow(uint32_t fid){
    return debug_mode?(debug_all_flows||flows_to_debug_set.count(fid)):false;
}


bool debug_queue(uint32_t qid){
    return debug_mode?(debug_all_queues||queues_to_debug_set.count(qid)):false;
}

bool debug_host(uint32_t qid){
    return debug_mode?(debug_all_hosts||hosts_to_debug_set.count(qid)):false;
}

bool debug(){
    return debug_mode;
}

bool print_flow_result(){
    return print_flow;
}
