#!/bin/sh
while [ -n "$(cat /proc/swaps | grep /dev/rmem0)" ]
do
  swapoff /dev/rmem0
done

while [ -n "$(lsmod | grep rmem)" ]
do
  rmmod rmem
done

while [ -d "swap" ]
do
  rmdir swap
done

