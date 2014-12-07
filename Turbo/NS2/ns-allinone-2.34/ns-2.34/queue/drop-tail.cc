/* -*-	Mode:C++; c-basic-offset:8; tab-width:8; indent-tabs-mode:t -*- */
/*
 * Copyright (c) 1994 Regents of the University of California.
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
 *	This product includes software developed by the Computer Systems
 *	Engineering Group at Lawrence Berkeley Laboratory.
 * 4. Neither the name of the University nor of the Laboratory may be used
 *    to endorse or promote products derived from this software without
 *    specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE REGENTS AND CONTRIBUTORS ``AS IS'' AND
 * ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
 * IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
 * ARE DISCLAIMED.  IN NO EVENT SHALL THE REGENTS OR CONTRIBUTORS BE LIABLE
 * FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
 * DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS
 * OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
 * HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
 * LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY
 * OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
 * SUCH DAMAGE.
 */

#ifndef lint
static const char rcsid[] =
    "@(#) $Header: /cvsroot/nsnam/ns-2/queue/drop-tail.cc,v 1.17 2004/10/28 23:35:37 haldar Exp $ (LBL)";
#endif

#include "drop-tail.h"

static class DropTailClass : public TclClass {
	public:
		DropTailClass() : TclClass("Queue/DropTail") {}
		TclObject* create(int, const char*const*) {
			return (new DropTail);
		}
	} class_drop_tail;

void DropTail::reset()
{
	Queue::reset();
}

int DropTail::gqid = 0;

int DropTail::command(int argc, const char*const* argv) 
{
	if (argc==2) {
		if (strcmp(argv[1], "printstats") == 0) {
			print_summarystats();
			return (TCL_OK);
		}
 		if (strcmp(argv[1], "shrink-queue") == 0) {
 			shrink_queue();
 			return (TCL_OK);
 		}
	}
	if (argc == 3) {
		if (!strcmp(argv[1], "packetqueue-attach")) {
			delete q_;
			if (!(q_ = (PacketQueue*) TclObject::lookup(argv[2])))
				return (TCL_ERROR);
			else {
				pq_ = q_;
				return (TCL_OK);
			}
		}
	}
	return Queue::command(argc, argv);
}

/*
 * drop-tail
 */
void DropTail::enque(Packet* p)
{
  //printf ("%f Enqueue called on queue %d lim:%d\n", Scheduler::instance().clock(), qid_, qlim_); fflush(stdout);
	if (summarystats) {
                Queue::updateStats(qib_?q_->byteLength():q_->length());
	}

	int qlimBytes = qlim_ * mean_pktsize_;
	if ((!qib_ && (q_->length() + 1) >= qlim_) || (qib_ && (q_->byteLength() + hdr_cmn::access(p)->size()) >= qlimBytes)){
		// if the queue would overflow if we added this packet...
		if (drop_front_) { /* remove from head of queue */
			q_->enque(p);
			Packet *pp = q_->deque();
			drop(pp);
		}else if (drop_prio_ == 1) {
			Packet *max_pp = p;
			int max_prio = 0;

			q_->enque(p);
			q_->resetIterator();
			for (Packet *pp = q_->getNext(); pp != 0; pp = q_->getNext()) {
				if (!qib_ || ( q_->byteLength() - hdr_cmn::access(pp)->size() < qlimBytes)) {
          				hdr_ip* h = hdr_ip::access(pp);
          				int prio = h->prio();
          				if (prio >= max_prio) {
            					max_pp = pp; 
            					max_prio = prio;
          				}   
				}   
			}   
			q_->remove(max_pp);
			drop(max_pp); 	
		}else if (drop_prio_ == 2) {
			// Turbo TCP dropping algorithm; THINK
			q_->enque(p);
			while (q_->byteLength() > qlimBytes) {
				Packet *p = worst_retx_prio_packet();
				q_->remove(p);
				drop(p);
			}
    		}else {
			drop(p);
		}
	}else{
		q_->enque(p);
	}
}

//AG if queue size changes, we drop excessive packets...
void DropTail::shrink_queue() 
{
        int qlimBytes = qlim_ * mean_pktsize_;
	if (debug_)
		printf("shrink-queue: time %5.2f qlen %d, qlim %d\n",
 			Scheduler::instance().clock(),
			q_->length(), qlim_);
        while ((!qib_ && q_->length() > qlim_) || 
            (qib_ && q_->byteLength() > qlimBytes)) {
                if (drop_front_) { /* remove from head of queue */
                        Packet *pp = q_->deque();
                        drop(pp);
                } else {
                        Packet *pp = q_->tail();
                        q_->remove(pp);
                        drop(pp);
                }
        }
}


// Picks the earliest packet of the flow that has p
Packet *DropTail::keep_order_packet(Packet *p)
{
	q_->resetIterator();
	hdr_ip* hp = hdr_ip::access(p);
	Packet *pp = q_->getNext();
	for (;pp != p; pp = q_->getNext()) {
		hdr_ip* h = hdr_ip::access(pp);
		if (h->saddr() == hp->saddr() 
			&& h->daddr() == hp->daddr()
			&& h->flowid() == hp->flowid()) {
      			break;
    		} 
  	}
  	return pp;
}

Packet* DropTail::worst_retx_prio_packet() 
{
	q_->resetIterator();
	Packet *p = q_->getNext();
	int lowest_retx_prio_ = hdr_ip::access(p)->retx_prio();
	int lowest_prio_ = hdr_ip::access(p)->prio();
	for (Packet *pp = q_->getNext(); pp!= 0; pp = q_->getNext()) {
		hdr_ip* h = hdr_ip::access(pp);
		int retx_prio = h->retx_prio();
    		//deque from the head
    		if (retx_prio < lowest_retx_prio_) {
      			p = pp;
      			lowest_retx_prio_ = retx_prio;
      			lowest_prio_ = h->prio();
    		} else if (retx_prio == lowest_retx_prio_) { // TODO: Not the best way
      			if (h->prio() > lowest_prio_) {
        		p = pp;
        		lowest_prio_ = h->prio();
      			}
    		}
  	}
  return p; 
}


Packet* DropTail::best_retx_prio_packet() 
{
	q_->resetIterator();
	Packet *p = q_->getNext();
	int highest_retx_prio_ = hdr_ip::access(p)->retx_prio();
	int highest_prio_ = hdr_ip::access(p)->prio();
	for (Packet *pp = q_->getNext(); pp!= 0; pp = q_->getNext()) {
		hdr_ip* h = hdr_ip::access(pp);
		int retx_prio = h->retx_prio();
    		//deque from the head
    		if (retx_prio > highest_retx_prio_) {
      			p = pp;
      			highest_retx_prio_ = retx_prio;
      			highest_prio_ = h->prio();
    		} else if (retx_prio == highest_retx_prio_) {
      			if (h->prio() < highest_prio_) {
        			p = pp;
        			highest_prio_ = h->prio();
      			}
    		}
  	}
  	//if (highest_retx_prio_ != 0) {
  	//  printf("Retransmission priority set to %d\n", highest_retx_prio_);
  	//}
  	return p; 
}


Packet* DropTail::deque(){
	if (summarystats && &Scheduler::instance() != NULL) {
    		Queue::updateStats(qib_?q_->byteLength():q_->length());
	}
  	// If Queue is empty return;
  	if (q_->length() <= 0) {
		return q_->deque();
	}
  
  	/*Shuang: deque the packet with the highest priority */
  	if (deque_prio_ == 1) {
		q_->resetIterator();
		Packet *p = q_->getNext();
		assert (p != 0);
		int highest_prio_;
		highest_prio_ = hdr_ip::access(p)->prio();
		for (Packet *pp = q_->getNext(); pp != 0; pp = q_->getNext()) {
			hdr_ip* h = hdr_ip::access(pp);
			int prio = h->prio();
			//deque from the head
			if (prio < highest_prio_) {
				p = pp;
				highest_prio_ = prio;
        		}
      		}
      		if (keep_order_) { // If the earliest packet of the best flow needs to be scheduled
        		p = keep_order_packet(p);
      		}
      		q_->remove(p);
      		return p;
  	}else if (deque_prio_ == 2) {
		// Gautam: Algorithm that keeps retransmitted packets at higher priority
    		Packet *p = best_retx_prio_packet();
    		if (keep_order_) {
      			p = keep_order_packet(p);
    		}
    		q_->remove(p);
    		return p;
  	}else {
		return q_->deque();
	}
}

void DropTail::print_summarystats()
{
	//double now = Scheduler::instance().clock();
        printf("True average queue: %5.3f", true_ave_);
        if (qib_)
                printf(" (in bytes)");
        printf(" time: %5.3f\n", total_time_);
}
