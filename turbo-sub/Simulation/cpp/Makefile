
CC=g++ -std=c++0x
CFLAGS=-g -O3 -Wall

all: simulator

simulator: main.o node.o queue.o turboqueue.o flow.o pacedflow.o turboflow.o turboflow_perpkt.o packet.o event.o topology.o simpletopology.o params.o factory.o random_variable.o singlelinkexperiment.o pfabricexperiment.o continuousModelExperiment.o fixedDistributionExperiment.o
	$(CC) $(CFLAGS) -Wall main.o node.o queue.o turboqueue.o flow.o pacedflow.o turboflow.o turboflow_perpkt.o packet.o event.o topology.o simpletopology.o params.o factory.o random_variable.o singlelinkexperiment.o pfabricexperiment.o continuousModelExperiment.o fixedDistributionExperiment.o -o simulator

params.o: params.cpp
	$(CC) $(CFLAGS) -c -Wall params.cpp
main.o: main.cpp
	$(CC) $(CFLAGS) -c -Wall main.cpp
singlelinkexperiment.o: singlelinkexperiment.cpp
	$(CC) $(CFLAGS) -c -Wall singlelinkexperiment.cpp
pfabricexperiment.o: pfabricexperiment.cpp
	$(CC) $(CFLAGS) -c -Wall pfabricexperiment.cpp
continuousModelExperiment.o: continuousModelExperiment.cpp
	$(CC) $(CFLAGS) -c -Wall continuousModelExperiment.cpp
fixedDistributionExperiment.o: fixedDistributionExperiment.cpp
	$(CC) $(CFLAGS) -c -Wall fixedDistributionExperiment.cpp
node.o: node.cpp
	$(CC) $(CFLAGS) -c -Wall node.cpp

topology.o: topology.cpp
	$(CC) $(CFLAGS) -c -Wall topology.cpp
simpletopology.o: simpletopology.cpp
	$(CC) $(CFLAGS) -c -Wall simpletopology.cpp


queue.o: queue.cpp
	$(CC) $(CFLAGS) -c -Wall queue.cpp
turboqueue.o: turboqueue.cpp
	$(CC) $(CFLAGS) -c -Wall turboqueue.cpp


flow.o: flow.cpp
	$(CC) $(CFLAGS) -c -Wall flow.cpp
pacedflow.o: pacedflow.cpp
	$(CC) $(CFLAGS) -c -Wall pacedflow.cpp
turboflow.o: turboflow.cpp
	$(CC) $(CFLAGS) -c -Wall turboflow.cpp

turboflow_perpkt.o: turboflow_perpkt.cpp
	$(CC) $(CFLAGS) -c -Wall turboflow_perpkt.cpp

packet.o: packet.cpp
	$(CC) $(CFLAGS) -c -Wall packet.cpp

event.o: event.cpp
	$(CC) $(CFLAGS) -c -Wall event.cpp

random_variable.o: random_variable.cpp
	$(CC) $(CFLAGS) -c -Wall random_variable.cpp

factory.o: factory.cpp
	$(CC) $(CFLAGS) -c -Wall factory.cpp

clean:
	rm -rf *o simulator
	make
