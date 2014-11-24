/* -*-  Mode:C++; c-basic-offset:8; tab-width:8; indent-tabs-mode:t -*- */
/*
 * Copyright (c) 2000  International Computer Science Institute
 * All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions
 * are met:
 * 1. Redistributions of source code must retain the above copyright
 *    notice, this list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright
 *    notice, this list of conditions and the following disclaimer in the
 *    documentation and/or other materials provided with the distribution.
 * 3. All advertising materials mentioning features or use of this software
 *    must display the following acknowledgement:
 *	This product includes software developed by ACIRI, the AT&T 
 *      Center for Internet Research at ICSI (the International Computer
 *      Science Institute).
 * 4. Neither the name of ACIRI nor of ICSI may be used
 *    to endorse or promote products derived from this software without
 *    specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY ICSI AND CONTRIBUTORS ``AS IS'' AND
 * ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
 * IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
 * ARE DISCLAIMED.  IN NO EVENT SHALL ICSI OR CONTRIBUTORS BE LIABLE
 * FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
 * DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS
 * OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
 * HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
 * LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY
 * OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
 * SUCH DAMAGE.
 *
 */

#ifndef ns_logging_data_struct_h
#define ns_logging_data_struct_h

#include "node.h"
#include "packet.h"
#include "route.h"
#include "rate-estimator.h"
#include "pushback-constants.h"

class LoggingDataStructNode {
 public:
  int nid_;      //the neighbors id.
  RateEstimator * rateEstimator_;

  int pushbackSent_;  //whether pushback message was sent to this neighbor
  double limit_;      //limit specified in the pushback message sent to it.
  
  //status details of this neighbor.
  int gotStatus_;   
  double statusArrivalRate_;
  int countLessReportedRate_;   //variable used to protect low senders
    
  int sentRefresh_; //whether we have sent a refresh to this neighbor yet.

  LoggingDataStructNode * next_;
  
  LoggingDataStructNode(int id, LoggingDataStructNode * next); 
  ~LoggingDataStructNode();
  
  void sentRefresh(double limit);
  void pushbackSent(double limit, double expectedStatusRate);
  void registerStatus(double arrRate);
  void log(Packet *pkt);
};


class LoggingDataStruct {

 public:
  LoggingDataStructNode * first_;
  int count_;       //number of members in this struct
  int myID_;        // id of the my node, needed to figure out who sent the pkt.

  RateEstimator * rateEstimator_;   // rate estimator for all bytes coming in for this RLS.

  double reset_time_;  //time when logging was last reset.

  //consolidated status details.
  int gotStatusAll_;
  double statusArrivalRateAll_;

  RouteLogic * rtLogic_;
  
  LoggingDataStruct(Node *, RouteLogic *, int sampleAddress, double estimate);
  ~LoggingDataStruct();

  void log(Packet * pkt);
  int consolidateStatus();
  void registerStatus(int sender, double arrRate);
  LoggingDataStructNode * getNodeByID(int id);
  void resetStatus();
};

#endif
