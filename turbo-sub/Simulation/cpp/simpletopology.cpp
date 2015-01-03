
#include "simpletopology.h"

extern DCExpParams params;


/*
 * Declaration for a single link topology
 * A -- B egress queues at A and B
 */
SingleLinkTopology::SingleLinkTopology(double bandwidth, double drop_prob) {
  src = new Host(0, bandwidth, DROPTAIL_QUEUE);
  dst = new Host(1, bandwidth, DROPTAIL_QUEUE);

  // Modify the queue
  src->queue = Factory::get_queue(0, bandwidth, params.queue_size,
                                  PROB_DROP_QUEUE, drop_prob, 0);

  // Create the link
  src->queue->set_src_dst(src, dst);
  dst->queue->set_src_dst(dst, src);
}

Queue * SingleLinkTopology::get_next_hop(Packet *p, Queue *q) {
  return NULL; // signifies packet arrival event
}

double SingleLinkTopology::get_oracle_fct(Flow *f) {
  double propagation_delay = 2 * 1000000.0 * f->src->queue->propagation_delay;
    //in us (host delay + switch delay)
  double bandwidth = f->src->queue->rate / 1000000.0; // For us
  uint32_t np = ceil(f->size / f->mss); // TODO: Must be a multiple of 1460
  double transmission_delay = (np * (f->mss + f->hdr_size) + f->hdr_size) * 8
                               / bandwidth; //us;
                              //  40 * 8 for ack
  return propagation_delay + transmission_delay;
}


/*
 * Declaration for a single link topology
 * A -- Sw -- B egress queues at A, B and Switch
 */

SingleSenderReceiverTopology::SingleSenderReceiverTopology(
  double bandwidth, double drop_prob) {

  src = new Host(0, bandwidth, DROPTAIL_QUEUE);
  dst = new Host(1, bandwidth, DROPTAIL_QUEUE);
  sw = new CoreSwitch(0, 2, bandwidth, DROPTAIL_QUEUE);

  // Modify the second queue of the switch to drop packets
  sw->queues[1] = Factory::get_queue(0, bandwidth, params.queue_size,
                                     PROB_DROP_QUEUE, drop_prob, 0);

  // Create the link
  src->queue->set_src_dst(src, sw);
  dst->queue->set_src_dst(dst, sw);
  sw->queues[0]->set_src_dst(sw, src);
  sw->queues[1]->set_src_dst(sw, dst);
}

Queue * SingleSenderReceiverTopology::get_next_hop(Packet *p, Queue *q) {
  if (q->dst->type == HOST) {
    return NULL; // Packet Arrival
  }
  // At host level for N->1 topology
  assert(q->src->type == HOST);
  if (p->src->id == 0) {
    return ((Switch *) q->dst)->queues[1];
  } else if (p->src->id == 1) {
    return ((Switch *) q->dst)->queues[0];
  }
  assert(false);
}

double SingleSenderReceiverTopology::get_oracle_fct(Flow *f) {
  double propagation_delay = 4 * 1000000.0 * f->src->queue->propagation_delay;
    //in us (host delay + switch delay)
  double bandwidth = f->src->queue->rate / 1000000.0; // For us
  uint32_t np = ceil(f->size / f->mss); // TODO: Must be a multiple of 1460
  double transmission_delay = ((np + 1) * (f->mss + f->hdr_size)
                               + 2.0 * f->hdr_size)
                               * 8 / bandwidth;
  return propagation_delay + transmission_delay;
}


/*
 *Declaration for N to one topology
 */

NToOneTopology::NToOneTopology(uint32_t num_senders, double bandwidth) {
  this->num_senders = num_senders;
  // Create Hosts
  for (uint32_t i = 0; i < num_senders; i++) {
    senders.push_back(new Host(i, bandwidth, params.queue_type));
  }
  receiver = new Host(num_senders, bandwidth, params.queue_type);

  // Create switch
  sw = new CoreSwitch(0, num_senders + 1, bandwidth, params.queue_type);

  //Connect host queues
  for (uint32_t i = 0; i < num_senders; i++) {
    senders[i]->queue->set_src_dst(senders[i], sw);
  //  std::cout << "Linking Host " << i << " to Switch \n";
  }
  receiver->queue->set_src_dst(receiver, sw);

  // Connect switch queues
  for (uint32_t i = 0; i < num_senders; i++) {
    Queue *q = sw->queues[i];
    q->set_src_dst(sw, senders[i]);
  }
  sw->queues[num_senders]->set_src_dst(sw, receiver);
  sw->queues[num_senders]->interested = true;

}

Queue * NToOneTopology::get_next_hop(Packet *p, Queue *q) {
  if (q->dst->type == HOST) {
    return NULL; // Packet Arrival
  }
  // At host level for N->1 topology
  assert(q->src->type == HOST);
  if (p->src->id < num_senders) {
    return ((Switch *) q->dst)->queues[num_senders];
  } else {
    return ((Switch *) q->dst)->queues[p->dst->id];
  }
  assert(false);
}

 double NToOneTopology::get_oracle_fct(Flow *f) {
   double propagation_delay = 4 * 1000000.0 * f->src->queue->propagation_delay;
   double bandwidth = f->src->queue->rate / 1000000.0; // For us;
   uint32_t np = ceil(f->size / f->mss); // TODO: Must be a multiple of 1460
   double transmission_delay = ((np + 1) * (f->mss + f->hdr_size)
                               + 2.0 * f->hdr_size) // ACK has to travel two hops
                               * 8.0 / bandwidth; // us
                               //np+1 due to store and forward
  //printf("TD: %f PD: %f\n", transmission_delay, propagation_delay);
  return propagation_delay + transmission_delay;

 }
