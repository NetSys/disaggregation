#!/bin/sh
for s in $(ls /dev/rmem*)
do
  while [ -n "$(cat /proc/swaps | grep $s)" ]
  do
    swapoff -a
  done
done

while [ -n "$(lsmod | grep rmem)" ]
do
  rmmod rmem
done


