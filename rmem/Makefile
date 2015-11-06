obj-m := rmem.o
KDIR := /lib/modules/$(shell uname -r)/build
PWD := $(shell pwd)

make:
	$(MAKE) -C $(KDIR) SUBDIRS=$(PWD) modules
	gcc fetch.c -o fetch
	gcc parse.c -o parse

clean:
	$(MAKE) -C $(KDIR) SUBDIRS=$(PWD) clean
	rm fetch parse

