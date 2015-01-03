/*
 * Copyright (c) 1993-1994 Regents of the University of California.
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
 *      This product includes software developed by the University of
 *      California, Berkeley and the Network Research Group at
 *      Lawrence Berkeley Laboratory.
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
static const char rcsid[] =
    "@(#) $Header: /cvsroot/otcl-tclcl/tclcl/timer.cc,v 1.4 1997/09/27 10:19:52 tecklee Exp $ (LBL)";

extern "C" {
#include <sys/types.h>
#ifndef WIN32
#include <sys/time.h>
#endif        
}
#include "tclcl.h"
#include "timer.h"

Timer::Timer() : token_(0)
{
}

Timer::~Timer()
{
	if (token_ != 0) 
		cancel();
}

void Timer::msched(int ms)
{
	if (token_) Tcl_DeleteTimerHandler(token_);
	token_ = Tcl_CreateTimerHandler(ms, dispatch, (ClientData)this);
}

void Timer::dispatch(ClientData cd)
{
	Timer* t = (Timer*)cd;
	t->token_ = 0;
	t->timeout();
}

void Timer::cancel()
{
	if (token_ != 0) {
		Tcl_DeleteTimerHandler(token_);
		token_ = 0;
	}
}

double Timer::gettimeofday() const
{
	timeval tv;
	::gettimeofday(&tv, 0);
	return (1e6 * double(tv.tv_sec) + double(tv.tv_usec));
}

