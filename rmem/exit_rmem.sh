#!/bin/sh
while [ -n "$(cat /proc/swaps | grep /dev/rmem0)" ]
do
  sudo swapoff /dev/rmem0
done

while [ -n "$(lsmod | grep rmem)" ]
do
  sudo rmmod rmem
done

free > /dev/null && sync && echo 3 > /proc/sys/vm/drop_caches && free > /dev/null;
