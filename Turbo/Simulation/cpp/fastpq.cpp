/*
 * fastpq.cpp
 *
 *  Created on: Dec 17, 2014
 *      Author: peter
 */
#include "fastpq.h"
#include "assert.h"


FastPQ::FastPQ(){
	timebase = 0;
	head = 0;
	count = 0;
	length = 0;
}


void FastPQ::push(Event* evt)
{
	int timekey = int(evt->time * FASTPQ_GRANULARITY);
	assert(timekey >= timebase);

	int offset = timekey - timebase;
	assert(offset < FASTPQ_MAX_EVT_DURATION);
	if(offset + 1 > length)
		length = offset + 1;
	event_queue[(head +offset) % FASTPQ_MAX_EVT_DURATION].push(evt);
	count++;
}

Event* FastPQ::front()
{
	if(length){
		return NULL;
	}else
		return NULL;
}



