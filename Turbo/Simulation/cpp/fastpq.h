#ifndef FASTPQ_H
#define FASTPQ_H

#include <queue>
#include "event.h"

//Fast priority queue
class FastPQ
{
#define FASTPQ_MAX_EVT_DURATION 10000000000
#define FASTPQ_GRANULARITY 1000000000
private:
	std::queue<Event*> event_queue[FASTPQ_MAX_EVT_DURATION];
	int timebase;
	int head;
	int length;
	int count;

public:
	FastPQ();
	void push(Event * evt);
	Event* front();



};

#endif
