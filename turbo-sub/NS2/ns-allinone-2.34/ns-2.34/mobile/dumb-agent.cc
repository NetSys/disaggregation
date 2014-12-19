
/*
 * dumb-agent.cc
 * Copyright (C) 2000 by the University of Southern California
 * $Id: dumb-agent.cc,v 1.3 2006/02/22 13:32:23 mahrenho Exp $
 *
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License,
 * version 2, as published by the Free Software Foundation.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License along
 * with this program; if not, write to the Free Software Foundation, Inc.,
 * 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.
 *
 *
 * The copyright of this module includes the following
 * linking-with-specific-other-licenses addition:
 *
 * In addition, as a special exception, the copyright holders of
 * this module give you permission to combine (via static or
 * dynamic linking) this module with free software programs or
 * libraries that are released under the GNU LGPL and with code
 * included in the standard release of ns-2 under the Apache 2.0
 * license or under otherwise-compatible licenses with advertising
 * requirements (or modified versions of such code, with unchanged
 * license).  You may copy and distribute such a system following the
 * terms of the GNU GPL for this module and the licenses of the
 * other code concerned, provided that you include the source code of
 * that other code when and as the GNU GPL requires distribution of
 * source code.
 *
 * Note that people who make modified versions of this module
 * are not obligated to grant this special exception for their
 * modified versions; it is their choice whether to do so.  The GNU
 * General Public License gives permission to release a modified
 * version without this exception; this exception also makes it
 * possible to release a modified version which carries forward this
 * exception.
 *
 */

// dumb-agent.cc

#include "dumb-agent.h"

static class DumbAgentClass : public TclClass {
public:
  DumbAgentClass() : TclClass("Agent/DumbAgent") {}
  TclObject* create(int, const char*const*) {
    return (new DumbAgent());
  }
} class_DumbAgent;

DumbAgent::DumbAgent() : Agent(PT_PING) {}


int DumbAgent::command(int argc, const char*const* argv)
{
  if (argc == 3) {
    if (strcmp(argv[1], "port-dmux") == 0) {
      dmux_ = (PortClassifier *)TclObject::lookup (argv[2]);
      if (dmux_ == 0) {
	fprintf (stderr, "%s: %s lookup of %s failed\n", __FILE__, argv[1],
		 argv[2]);
	return TCL_ERROR;
      }
      return TCL_OK;
    }
    else if (strcmp(argv[1], "tracetarget") == 0) {
      tracetarget_ = (Trace *)TclObject::lookup (argv[2]);
      if (tracetarget_ == 0) {
	fprintf (stderr, "%s: %s lookup of %s failed\n", __FILE__, argv[1],
		 argv[2]);
	return TCL_ERROR;
      }
      return TCL_OK;
    }
  }
  return Agent::command(argc, argv);
}
 

void DumbAgent::recv(Packet *p, Handler *h=0) 
{
  
  hdr_cmn *ch = HDR_CMN(p);
  hdr_ip *iph = HDR_IP(p);
  
  if (ch->direction() == hdr_cmn::UP) { // in-coming pkt
    if ((u_int32_t)iph->daddr() == IP_BROADCAST) {
//      printf("Recvd brdcast pkt\n");
      dmux_->recv(p, 0);
    
    } else {
      // this agent recvs pkts destined to it only
      // doesnot support multi-hop scenarios
      assert(iph->daddr() == here_.addr_);
//      printf("Recvd unicast pkt\n");
      dmux_->recv(p, 0);
    }
    
  } else { // out-going pkt
    target_->recv(p, (Handler*)0);
  }

}
 
void DumbAgent::trace(char *fmt, ...) 
{
  
  va_list ap;
  
  if (!tracetarget_)
    return;
  
  va_start (ap, fmt);
  vsprintf (tracetarget_->pt_->buffer (), fmt, ap);
  tracetarget_->pt_->dump ();
  va_end (ap);
}
