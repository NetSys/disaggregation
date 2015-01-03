#!/bin/sh
while [ -n "$(cat /proc/swaps | grep /dev/rmem0)" ]
do
  sudo swapoff /dev/rmem0
done

while [ -n "$(lsmod | grep rmem)" ]
do
  sudo rmmod rmem
done

while [ -d "swap" ]
do
  rmdir swap
done
