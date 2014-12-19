#ifndef TURBO_FLOW_PER_PKT_H
#define TURBO_FLOW_PER_PKT_H

#include "turboflow.h"


struct SendLogEntry {
  uint32_t seq_no;
  double timeout;
  bool active;
};

/* Uses Kaifei's per packet timeout logic
 * but has no inflation or probing mechanism
 */
class TurboFlowPerPacketTimeout : public TurboFlow {
public:
  TurboFlowPerPacketTimeout(uint32_t id, double start_time, uint32_t size,
                               Host *s, Host *d);
  virtual void send_pending_data();
  virtual void receive_ack(uint32_t ack, std::vector<uint32_t> sack_list);
  virtual void handle_timeout();
  virtual void reset_retx_timeout();
  virtual uint32_t select_next_packet();

  // double priority_backoff;
  std::vector<SendLogEntry> send_log;
  uint32_t head_of_log_idx;

  uint32_t packet_num;

  uint32_t retx_event_packet_num; // Pkt log on which the current retx
                                  // event is set

  std::unordered_map<uint32_t, bool> received_ack;
};


/* Uses Kaifei's per packet timeout logic
 * and uses INT_MAX as inflation and probing
 */
/*
class TurboFlowPerPacketTimeoutWithProbing : public TurboFlowPerPacketTimeout {
public:
  TurboFlowPerPacketTimeoutWithProbing(uint32_t id, double start_time, uint32_t size,
                               Host *s, Host *d);
  virtual void send_pending_data();
  virtual void receive_ack(uint32_t ack);
  virtual void handle_timeout();
  virtual uint32_t get_priority(uint32_t seq);
  virtual Packet* send_probe(bool direction);
  virtual void receive_probe(Probe *p);

  uint32_t get_real_priority(uint32_t seq);

};
*/

/*

*/
/*
class TurboFlowPerPacketTimeoutWithRareProbing : public TurboFlowPerPacketTimeoutWithProbing {
public:
  TurboFlowPerPacketTimeoutWithRareProbing(uint32_t id, double start_time, uint32_t size, Host *s, Host *d);
  virtual void send_pending_data();

  double last_probe_sending_time;
};
*/
#endif
