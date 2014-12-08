################################################################################
#
# Intel 82599 Virtual Function driver
# Copyright(c) 1999 - 2012 Intel Corporation.
#
# This program is free software; you can redistribute it and/or modify it
# under the terms and conditions of the GNU General Public License,
# version 2, as published by the Free Software Foundation.
#
# This program is distributed in the hope it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
# more details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin St - Fifth Floor, Boston, MA 02110-1301 USA.
#
# The full GNU General Public License is included in this distribution in
# the file called "COPYING".
#
# Contact Information:
# e1000-devel Mailing List <e1000-devel@lists.sourceforge.net>
# Intel Corporation, 5200 N.E. Elam Young Parkway, Hillsboro, OR 97124-6497
#
################################################################################

#
# Makefile for the Intel(R) 82599 VF ethernet driver
#

###########################################################################
# Driver files
DRIVER_NAME=ixgbevf

# core driver files
$(DRIVER_NAME)-CFILES = ixgbevf_main.c ixgbevf_param.c ixgbevf_ethtool.c \
	                kcompat.c \
                        ixgbe_vf.c ixgbe_mbx.c
$(DRIVER_NAME)-HFILES = ixgbevf.h ixgbe_vf.h ixgbe_common.h ixgbe_mbx.h

# extra flags for module builds
EXTRA_CFLAGS += -DDRIVER_$(shell echo $(DRIVER_NAME) | tr '[a-z]' '[A-Z]')
EXTRA_CFLAGS += -DDRIVER_NAME=$(DRIVER_NAME)
EXTRA_CFLAGS += -DDRIVER_NAME_CAPS=$(shell echo $(DRIVER_NAME) | tr '[a-z]' '[A-Z]')
EXTRA_CFLAGS += -DAMAZON_NOHW_VLAN


obj-$(CONFIG_AMAZON_IXGBEVF) += $(DRIVER_NAME).o

$(DRIVER_NAME)-objs := $($(DRIVER_NAME)-CFILES:.c=.o)

clean:
ifeq ($(KOBJ),$(KSRC))
	$(MAKE) -C $(KSRC) SUBDIRS=$(shell pwd) clean
else
	$(MAKE) -C $(KSRC) O=$(KOBJ) SUBDIRS=$(shell pwd) clean
endif
	rm -rf $(TARGET) $(TARGET:.ko=.o) $(TARGET:.ko=.mod.c) $(TARGET:.ko=.mod.o) $(CFILES:.c=.o) $(MANFILE).gz .*cmd .tmp_versions
