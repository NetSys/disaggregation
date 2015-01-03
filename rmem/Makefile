obj-m := rmem.o
KDIR := /lib/modules/$(shell uname -r)/build
PWD := $(shell pwd)

make:
	$(MAKE) -C $(KDIR) SUBDIRS=$(PWD) modules

clean:
	$(MAKE) -C $(KDIR) SUBDIRS=$(PWD) clean

