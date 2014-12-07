#!/bin/sh
while true; do
    file=$(inotifywait -r /home/peter/disaggregation/rmem/*.c --format %w -q | sed -e "s,/home/peter/disaggregation/rmem/,,g" | tr '\n' ' ')
    echo $file
    ssh root@c7 "rm /root/disaggregation/rmem/$file"
    rsync -rv --update --include='*/' --include='*.c' --exclude='*' /home/peter/disaggregation/rmem/* root@c7:/root/disaggregation/rmem
done
