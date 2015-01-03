/* -*-	Mode:C++; c-basic-offset:8; tab-width:8; indent-tabs-mode:t -*-
 *
 * Copyright (c) 1997 Regents of the University of California.
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
 *
 * $Header: /cvsroot/nsnam/ns-2/trace/cmu-trace.h,v 1.28 2009/01/15 06:23:49 tom_henderson Exp $
 */

/* Ported from CMU/Monarch's code, nov'98 -Padma.*/

#ifndef __cmu_trace__
#define __cmu_trace__

#include "trace.h"
#include "god.h"

#ifndef __PRETTY_FUNCTION__
#define __PRETTY_FUNCTION__ ("")
#endif /* !__PRETTY_FUNCTION__ */

/* ======================================================================
   Global Defines
   ====================================================================== */
#define	DROP            'D'
#define	RECV            'r'
#define	SEND    	's'
#define	FWRD    	'f'

// change wrt Mike's code
#define EOT             'x'



#define TR_ROUTER	0x01
#define TR_MAC		0x02
#define TR_IFQ		0x04
#define TR_AGENT	0x08

#define TR_PHY		0x10

#define DROP_END_OF_SIMULATION		"END"
#define	DROP_MAC_COLLISION		"COL"
#define DROP_MAC_DUPLICATE		"DUP"
#define DROP_MAC_PACKET_ERROR		"ERR"
#define DROP_MAC_RETRY_COUNT_EXCEEDED	"RET"
#define DROP_MAC_INVALID_STATE		"STA"
#define DROP_MAC_BUSY			"BSY"
#define DROP_MAC_INVALID_DST            "DST"
#define DROP_MAC_SLEEP                  "SLP"   // smac sleep state

#define DROP_RTR_NO_ROUTE		"NRTE"  // no route
#define DROP_RTR_ROUTE_LOOP		"LOOP"  // routing loop
#define DROP_RTR_TTL                    "TTL"   // ttl reached zero
#define DROP_RTR_QFULL                  "IFQ"   // queue full
#define DROP_RTR_QTIMEOUT               "TOUT"  // packet expired
#define DROP_RTR_MAC_CALLBACK           "CBK"   // MAC callback
#define DROP_RTR_SALVAGE	        "SAL"

#define DROP_IFQ_QFULL                  "IFQ"   // no buffer space in IFQ
#define DROP_IFQ_ARP_FULL               "ARP"   // dropped by ARP
#define DROP_IFQ_FILTER                 "FIL"

#define DROP_OUTSIDE_SUBNET             "OUT"   // dropped by base stations if received rtg updates from nodes outside its domain.

#define MAX_ID_LEN	3
#define MAX_NODE	4096

/**
 * This class allows a dynamic library to define the tracing format
 * for newly defined packet types 
 * 
 */
class PacketTracer
{
	public:
		PacketTracer();
        	virtual ~PacketTracer();
		void setNext(PacketTracer *next);
		PacketTracer *getNext();
		int format_unknow(Packet *p, int offset, BaseTrace *pt_, int newtrace);
	protected:
		virtual int format(Packet *p, int offset, BaseTrace *pt_, int newtrace) = 0;	//return 0 if the packet is unknown
		PacketTracer *next_;
};


class CMUTrace : public Trace {
public:
	CMUTrace(const char *s, char t);
	void	recv(Packet *p, Handler *h);
	void	recv(Packet *p, const char* why);

	static void addPacketTracer(PacketTracer *pt);


private:
	char	tracename[MAX_ID_LEN + 1];
	int	nodeColor[MAX_NODE];
        int     tracetype;
        MobileNode *node_;
	int     newtrace_;

	//<zheng: ns 2.27 removed the following part, but we need it to control the broadcast radius>
        static double  bradius;
        static double  radius_scaling_factor_;
        static double  duration_scaling_factor_;
        static void calculate_broadcast_parameters();
	//</zheng>

        int initialized() { return node_ && 1; }
	int node_energy();
	int	command(int argc, const char*const* argv);
	void	format(Packet *p, const char *why);

        void    nam_format(Packet *p, int offset);

	void	format_phy(Packet *p, int offset);
	
	void	format_mac_common(Packet *p, const char *why, int offset);
	void    format_mac(Packet *p, int offset);
	void    format_smac(Packet *p, int offset);
	void	format_ip(Packet *p, int offset);

	void	format_arp(Packet *p, int offset);
	void    format_hdlc(Packet *p, int offset);
	void	format_dsr(Packet *p, int offset);
	void	format_msg(Packet *p, int offset);
	void	format_tcp(Packet *p, int offset);
	void    format_sctp(Packet *p, int offset);
	void	format_rtp(Packet *p, int offset);
	void	format_tora(Packet *p, int offset);
        void    format_imep(Packet *p, int offset);
        void    format_aodv(Packet *p, int offset);
	void    format_aomdv(Packet *p, int offset);

	// This holds all the tracers added at run-time
	static PacketTracer *pktTrc_;

};

#endif /* __cmu_trace__ */
