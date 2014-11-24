#ifndef TURBO_FLOW_H
#define TURBO_FLOW_H

#include "flow.h"
#include <iostream>
#include <assert.h>
#include <list>
#include <set>
#include <stdint.h>
#include <limits>

const int INT_MAX = std::numeric_limits<int32_t>::max();


/* This class uses simple timeout logic; sends a probe on timeout but
 * keeps sending packets after timeout at INT_MAX priority until it recovers
 * from a new ack or a probe ack
 */
class TurboFlow : public PFabricFlow {
public:
  TurboFlow(uint32_t id, double start_time, uint32_t size,
    Host *s, Host *d);
  virtual void send_pending_data();
  void receive_ack(uint32_t ack, std::vector<uint32_t> sack_list);
  virtual void receive_probe(Probe *p);
  virtual void receive(Packet *p);
  virtual void handle_timeout();
  virtual Packet* send_probe(bool direction);
  void reset_retx_timeout();
  virtual uint32_t get_priority(uint32_t seq);
  uint32_t get_real_priority(uint32_t seq);

  void cancel_flow_proc_event();

  bool in_probe_mode;
  bool should_send_probe;
};

/* This class uses simple timeout logic; sends a probe on timeout but
 * dosn't send packets and keeps probing per timeout until it recovers
 * from a new ack or a probe ack
 */
class TurboFlowStopOnTimeout : public TurboFlow {
public:
  TurboFlowStopOnTimeout(uint32_t id, double start_time, uint32_t size,
                         Host *s, Host *d);
  virtual void send_pending_data();
};


// struct SendLogEntry {
//   uint32_t seq_no;
//   double sending_time;
// };
//
// /* Uses Kaifei's per packet timeout logic
//  * but has no inflation or probing mechanism
//  */
// class TurboFlowPerPacketTimeout : public TurboFlow {
// public:
//   TurboFlowPerPacketTimeout(uint32_t id, double start_time, uint32_t size,
//                                Host *s, Host *d);
//   virtual void send_pending_data();
//   virtual void receive_ack(uint32_t ack);
//   virtual void handle_timeout();
//   virtual void reset_retx_timeout();
//   virtual uint32_t select_next_packet();
//
//   // double priority_backoff;
//   std::list<SendLogEntry> in_flight_packets;
// };


/* Uses Kaifei's per packet timeout logic
 * and uses INT_MAX as inflation and probing
 */
// class TurboFlowPerPacketTimeoutWithProbing : public TurboFlowPerPacketTimeout {
// public:
//   TurboFlowPerPacketTimeoutWithProbing(uint32_t id, double start_time, uint32_t size,
//                                Host *s, Host *d);
//   virtual void send_pending_data();
//   virtual void receive(Packet *p);
//   virtual void receive_sack(uint32_t ack,
//     std::vector<uint32_t> sack_list);
//   virtual void handle_timeout();
//   virtual uint32_t get_priority(uint32_t seq);
//   virtual Packet* send_probe(bool direction);
//   virtual void receive_probe(Probe *p);
//
//   uint32_t get_real_priority(uint32_t seq);
//
// };

/*

*/
// class TurboFlowPerPacketTimeoutWithRareProbing : public TurboFlowPerPacketTimeoutWithProbing {
// public:
//   TurboFlowPerPacketTimeoutWithRareProbing(uint32_t id, double start_time, uint32_t size, Host *s, Host *d);
//   virtual void send_pending_data();
//
//   double last_probe_sending_time;
//
// };


/* Version of Turbo that automatically assigns inflated priority to all long flows
*/

class TurboFlowLongFlowsGetLowPriority : public TurboFlow {
public:
  TurboFlowLongFlowsGetLowPriority(uint32_t id, double start_time, uint32_t size, Host *s, Host *d);
  virtual uint32_t get_priority(uint32_t seq);
};

#endif
