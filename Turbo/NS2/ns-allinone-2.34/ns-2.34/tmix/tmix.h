/* -*-  Mode:C++; c-basic-offset:8; tab-width:8; indent-tabs-mode:t -*- */

/* 
 * Copyright 2007, Old Dominion University
 * Copyright 2007, University of North Carolina at Chapel Hill
 * 
 * Redistribution and use in source and binary forms, with or without 
 * modification, are permitted provided that the following conditions are met:
 * 
 *    1. Redistributions of source code must retain the above copyright 
 * notice, this list of conditions and the following disclaimer.
 *    2. Redistributions in binary form must reproduce the above copyright 
 * notice, this list of conditions and the following disclaimer in the 
 * documentation and/or other materials provided with the distribution.
 *    3. The name of the author may not be used to endorse or promote 
 * products derived from this software without specific prior written 
 * permission.
 * 
 * THIS SOFTWARE IS PROVIDED BY THE AUTHOR ``AS IS'' AND ANY EXPRESS OR 
 * IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED 
 * WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE 
 * DISCLAIMED. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY DIRECT, 
 * INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES 
 * (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR 
 * SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) 
 * CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, 
 * STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN 
 * ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE 
 * POSSIBILITY OF SUCH DAMAGE.
 *
 * M.C. Weigle, P. Adurthi, F. Hernandez-Campos, K. Jeffay, and F.D. Smith, 
 * Tmix: A Tool for Generating Realistic Application Workloads in ns-2, 
 * ACM Computer Communication Review, July 2006, Vol 36, No 3, pp. 67-76.
 * 
 * Contact: Michele Weigle (mweigle@cs.odu.edu)
 * 
 * For more information on Tmix and to obtain Tmix tools and 
 * connection vectors, see http://netlab.cs.unc.edu/Tmix
 */

#ifndef ns_tmix_h
#define ns_tmix_h

#include "timer-handler.h"
#include "app.h"
#include "node.h"
#include <string>
#include <stack>
#include <queue>
#include <map>
#include <vector>
#include <list>

#define MAX_NODES 10 

#define SEQ true     /* sequential connection vector */
#define CONC false   /* concurrent connection vector */
#define INITIATOR true
#define ACCEPTOR false
#define FIN 0
#define CVEC_LINE_MAX 100
#define CV_V1 1
#define CV_V2 2

class FullTcpAgent;
class Tmix;
class TmixTimer;
class TmixApp;
class ADU;
class ConnVector;

/*:::::::::::::::::::::::::: ADU class :::::::::::::::::::::::::::*/

/* Holds the size of the ADU (application data unit) and time-to-send delta.  
 * This is either some amount of time after the last ADU was sent (send_wait_) 
 * or after the last ADU was received (recv_wait_).
 */
class ADU 
{
public:
	ADU() : send_wait_(0), recv_wait_(0), size_(0) {};
	ADU(unsigned long send, unsigned long recv, unsigned long size) : 
		send_wait_(send), recv_wait_(recv), size_(size){};

	inline double get_send_wait_sec() {
		return send_wait_ / 1000000.0;   /* in seconds */
	}  
	inline double get_recv_wait_sec() {
		return recv_wait_ / 1000000.0;   /* in seconds */
	}
	inline unsigned long get_size() {return size_;}
	
	void print();

private:
	/* time (in usec) to wait after sending last ADU */
	unsigned long send_wait_;  
	/* time (in usec) to wait after receiving last ADU */
	unsigned long recv_wait_;  
	/* size (in bytes) of current ADU */
	unsigned long size_;
};

/*:::::::::::::::::::::::: CONNECTION VECTOR class :::::::::::::::::::::::::*/

/* Holds the attributes of a single connection */
class ConnVector
{
public:
	ConnVector() : global_id_(0), start_time_(0.0), init_win_(0),
		       acc_win_(0), type_(SEQ), init_ADU_count_(0),
		       acc_ADU_count_(0) {};

	ConnVector (unsigned long id, double start, bool type) : 
		global_id_(id), start_time_(start), init_win_(0), 
		acc_win_(0), type_(type),  init_ADU_count_(0), 
		acc_ADU_count_(0) {};

	ConnVector (unsigned long id, double start, bool type, 
		    int ninit, int nacc) : global_id_(id), start_time_(start),
					   init_win_(0), acc_win_(0),
					   type_(type), 
					   init_ADU_count_(ninit),
					   acc_ADU_count_(nacc) {};

	~ConnVector();

	inline unsigned long get_ID() {return global_id_;}
	inline double get_start_time() {return start_time_;}
	inline int get_init_win() {return init_win_;}
	inline int get_acc_win() {return acc_win_;}
	inline bool get_type() {return type_;}
	inline int get_init_ADU_count() {return init_ADU_count_;}
	inline int get_acc_ADU_count() {return acc_ADU_count_;}
	inline vector<ADU*> get_init_ADU() {return init_ADU_;}
	inline vector<ADU*> get_acc_ADU() {return acc_ADU_;}
	inline vector<ADU*>::iterator get_init_ADU_end() 
	{return init_ADU_.end();}
	inline vector<ADU*>::iterator get_acc_ADU_end() 
	{return acc_ADU_.end();}
  
	inline void set_init_win (int win, int pcktsz) {
		init_win_ = (int) (win / pcktsz);
	}
	inline void set_acc_win (int win, int pcktsz) {
		acc_win_ = (int) (win / pcktsz);
	}
	inline void incr_init_ADU_count () {init_ADU_count_++;}
	inline void incr_acc_ADU_count () {acc_ADU_count_++;}
	inline void set_init_ADU_count (int cnt) {init_ADU_count_ = cnt;}
	inline void set_acc_ADU_count (int cnt) {acc_ADU_count_ = cnt;}

	void add_ADU(ADU* adu, bool direction);
	void print();

private:
	unsigned long global_id_;
	double start_time_;
	int init_win_;          /* initiator's max window in packets */
	int acc_win_;           /* acceptor's max window in packets */
	bool type_;             /* SEQ or CONC */
	int init_ADU_count_;    /* number of ADUs for initiator */
	int acc_ADU_count_;     /* number of ADUs for acceptor */
	vector<ADU*> init_ADU_; /* vector of initiator's ADUs */
	vector<ADU*> acc_ADU_;  /* vector of acceptor's ADUs */
};

/*::::::::::::::::::::::::: TIMER HANDLER classes :::::::::::::::::::::::::::*/

class TmixAppTimer : public TimerHandler {
public:
	TmixAppTimer(TmixApp* t) : TimerHandler(), t_(t) {}
	virtual void handle(Event*);
	virtual void expire(Event*);
protected:
	TmixApp* t_;
};

class TmixTimer : public TimerHandler {
public:
	TmixTimer(Tmix* mgr) : TimerHandler(), mgr_(mgr) {}
	inline Tmix* mgr() {return mgr_;}
protected:
	virtual void handle(Event* e);
	virtual void expire(Event* e);
	Tmix* mgr_;	     
};

/*:::::::::::::::::::::::: TMIX APPLICATION class ::::::::::::::::::::*/

class TmixApp : public Application {
public:
	TmixApp() : Application(), id_(0), ADU_ind_(0), running_(false), 
			total_bytes_(0), expected_bytes_(0), timer_(this), 
			peer_(NULL), cv_(NULL), mgr_(NULL),
	                sent_last_ADU_(false), waiting_to_send_(false) {}
	~TmixApp();
	void timeout();
	void stop();
	void start();
	void recycle();
	bool send_first();

	inline const char* get_agent_name() {return agent_->name();}
	inline TmixApp* get_peer() {return peer_;}
	inline Tmix* get_mgr() {return (mgr_);}
	inline unsigned long get_id () {return id_;}
	inline bool get_running(){return running_;}
	inline Agent* get_agent(){return agent_;}
	inline bool get_type() {return type_;}
	inline int get_expected_bytes() {return expected_bytes_;}
	inline unsigned long get_global_id() {return cv_->get_ID();}
	ADU* get_current_ADU();
	inline bool sent_last_ADU() {return sent_last_ADU_;}
	inline bool waiting_to_send() {return waiting_to_send_;}
	inline ConnVector* get_cv() {return cv_;}

	inline void set_peer(TmixApp* peer) {peer_ = peer;}
	inline void set_agent(Agent* tcp) {agent_ = tcp;}
	inline void set_mgr(Tmix* mgr) {mgr_ = mgr;}
	inline void set_id (unsigned long id) {id_ = id;}
	inline void set_expected_bytes (int bytes) {expected_bytes_ = bytes;}
	inline void incr_expected_bytes (int bytes) {expected_bytes_ += bytes;}
	inline void set_adu_iter (vector<ADU*>::iterator adu) {ADU_iter_ = adu;}
	inline void set_cv (ConnVector* cv) {cv_ = cv;}
	inline void set_type (bool type) {type_ = type;}
	inline void print_cv() {cv_->print();}

	bool ADU_empty();
	bool end_of_ADU();
	char* id_str();

protected:
	void recv(int bytes);

	unsigned long id_;

	vector<ADU*>::iterator ADU_iter_; 
	int ADU_ind_;              /* index into the ADU vector */
	bool running_;

	bool type_;                /* initiator or acceptor */
           
	int total_bytes_;          /* total bytes received so far */
	int expected_bytes_;       /* total bytes expected from peer */

	TmixAppTimer timer_; 
	TmixApp* peer_;            /* pointer to the other side (init or acc */
	ConnVector* cv_;           /* pointer to the connection vector */
	Tmix* mgr_;       

	bool sent_last_ADU_;       /* sent the last ADU? */
	bool waiting_to_send_;     /* waiting to send something? */
};

/*::::::::::::::::::::::::: TMIX class :::::::::::::::::::::::::::::::::*/

class Tmix : public TclObject {
public:
	Tmix();
	~Tmix();

	void recycle (TmixApp*);
	void stop();
	void setup_connection();
  
	inline double now() {return Scheduler::instance().clock();}
	inline int get_active() {return active_connections_;}
	inline int get_total() {return total_connections_;}
	inline int running() {return running_;}
	inline int debug() {return debug_;}
	inline unsigned long get_ID() {return ID_;}
	inline int get_warmup() {return warmup_;} 
	inline FILE* get_outfp() {return outfp_;}
	inline double get_next_start() {return (*next_active_)->get_start_time();}
	inline bool scheduled_all() {return (next_active_ == connections_.end());}
	inline ConnVector* get_current_cvec() {return (ConnVector*) *next_active_;}

	inline void init_next_active() {next_active_ = connections_.begin();}
	void incr_next_active();

protected:
	virtual int command (int argc, const char*const* argv);
	void start();
	void recycle (FullTcpAgent*);

	ConnVector* read_one_cvec();
	ConnVector* read_one_cvec_v1();
	ConnVector* read_one_cvec_v2();
	void read_one_cvec_v1_helper(ConnVector * cv, ADU * adu, int last_state,
		unsigned long last_time_value, unsigned long last_initiator_time_value,
		unsigned long last_acceptor_time_value, bool pending_initiator, bool pending_acceptor);

	FullTcpAgent* picktcp();
	TmixApp* pickApp();	

	TmixTimer timer_;

	/* variables used to maintain array of acceptor and initiator nodes */
	int next_init_ind_;
	int next_acc_ind_;
	int total_nodes_;
	int current_node_;

	/* TCL configurable variables */
	string cvfn_;
	char line[CVEC_LINE_MAX];
	Node* initiator_[MAX_NODES];
	Node* acceptor_[MAX_NODES];
	char tcptype_[20];         /* {Reno, Tahoe, NewReno, SACK} */
	FILE* outfp_;
	FILE* cvfp_;               /* connection vector file pointer */
	int ID_;                   /* tmix cloud ID */
	int run_;                  /* exp run number (for RNG stream selection) */
	int debug_;
	int pkt_size_;
	unsigned long step_size_;  /* number of connections to read from cvfp_ 
				      at a time */
	int warmup_;               /* warmup interval (s) */

	unsigned long active_connections_;   /* number of active connections */
	unsigned long total_connections_;    /* number of total connections */
	unsigned long total_apps_;           /* number of total TmixApps */

	bool running_;              /* start new connections? */

	TclObject* lookup_obj(const char* name) {
		TclObject* obj = Tcl::instance().lookup(name);
		if (obj == NULL) 
			fprintf(stderr, "Bad object name %s\n", name);
		return obj;
	}

	/* Agent and App Pools */
	queue<FullTcpAgent*> tcpPool_;
	queue<TmixApp*> appPool_;

	/* string = tcpAgent's name */
	map<string, TmixApp*> appActive_;

	/* connection vectors */
	list<ConnVector*> connections_;

	/* points to the next connection to start */
	list<ConnVector*>::iterator next_active_;
};

#endif
