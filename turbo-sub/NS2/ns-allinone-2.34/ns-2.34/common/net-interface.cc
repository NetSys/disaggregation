/* -*-	Mode:C++; c-basic-offset:8; tab-width:8; indent-tabs-mode:t -*- */

/*
 * Copyright (C) 1997 by the University of Southern California
 * $Id: net-interface.cc,v 1.13 2005/08/25 18:58:02 johnh Exp $
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
/*
 * Ported by Polly Huang (USC/ISI), http://www-scf.usc.edu/~bhuang
 */

#ifndef lint
static const char rcsid[] =
    "@(#) $Header: /cvsroot/nsnam/ns-2/common/net-interface.cc,v 1.13 2005/08/25 18:58:02 johnh Exp $ (USC/ISI)";
#endif

#include "net-interface.h"

int NetworkInterface::command(int argc, const char*const* argv) {
	if (argc > 1) {
		if (strcmp(argv[1], "label") == 0) {
			if (argc == 2) {
				Tcl::instance().resultf("%d", intf_label_);
				return TCL_OK;
			}
			if (argc == 3) {
				intf_label_ = atoi(argv[2]);
				return TCL_OK;
			}
		}
	}
      	return (Connector::command(argc, argv));
}

void NetworkInterface::recv(Packet* p, Handler* h) {
	hdr_cmn* ch = hdr_cmn::access(p);
#ifdef LEO_DEBUG
	printf("Marking to %d\n", intf_label_);
#endif
	ch->iface() = intf_label_;
	ch->direction()= hdr_cmn::NONE; //direction: none
	send(p, h);
}

static class NetworkInterfaceClass : public TclClass {
public:
	NetworkInterfaceClass() : TclClass("NetworkInterface") {}
	TclObject* create(int, const char*const*) {
		return (new NetworkInterface);
	}
} class_networkinterface;

