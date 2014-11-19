#!/bin/sh

sudo swapoff /dev/rmem0
sudo rmmod rmem
rmdir swap
