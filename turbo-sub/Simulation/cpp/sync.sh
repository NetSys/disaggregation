#!/bin/sh
while true; do
    file=$(inotifywait -r *.cpp *.h *.py  *.sh experiments/fountain_experiments/*.py --format %w -q -e modify | sed -e "s,/home/peter/disaggregation/turbo-sub/Simulation/cpp/,,g" | tr '\n' ' ')
    echo $file
    ssh petergao@c33 "rm /home/eecs/petergao/disaggregation/turbo-sub/Simulation/cpp/$file" 
    rsync -rv --update --include='*/' --include='*.cpp' --include='*.h'  --include='*.sh'  --include='*.txt'  --include='*.py' --include='*.am' --exclude='*' /home/peter/disaggregation/turbo-sub/Simulation/cpp/* petergao@c33:/home/eecs/petergao/disaggregation/turbo-sub/Simulation/cpp/
#    rsync -r petergao@c33:/home/eecs/petergao/disaggregation/turbo-sub/Simulation/cpp/results/ /home/peter/disaggregation/turbo-sub/Simulation/cpp/results
done
