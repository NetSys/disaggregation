#!/bin/sh

swapoff /dev/rmem0
rmmod rmem
rmdir swap
