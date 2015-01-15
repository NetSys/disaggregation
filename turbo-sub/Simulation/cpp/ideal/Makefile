
CC=g++ -std=c++0x
CFLAGS=-g -O3 -Wall

all: ideal.out

ideal.out: ideal.cpp
	$(CC) $(CFLAGS) -Wall ideal.cpp -o ideal.out

clean:
	rm -rf *o ideal.out
	make
