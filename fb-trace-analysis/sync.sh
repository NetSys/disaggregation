#!/bin/sh
while true; do
    file=$(inotifywait -r /home/peter/disaggregation/fb-trace-analysis/*.py --format %w -q | sed -e "s,/home/peter/disaggregation/fb-trace-analysis/,,g" | tr '\n' ' ')
    echo $file
    ssh petergao@c33 "rm /home/eecs/petergao/disaggregation/fb-trace-analysis/$file"
    #scp -r /home/peter/disaggregation/fb-trace-analysis/*.py petergao@c33:/home/eecs/petergao/fb-trace-analysis
    rsync -rv --update --include='*/' --include='*.py' --exclude='*' /home/peter/disaggregation/fb-trace-analysis/* petergao@c33:/home/eecs/petergao/disaggregation/fb-trace-analysis
done
