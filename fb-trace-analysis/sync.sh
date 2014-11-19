while inotifywait -r /home/peter/disaggregation/fb-trace-analysis/*.py; do
    scp -r /home/peter/disaggregation/fb-trace-analysis/*.py petergao@c33:/home/eecs/petergao/fb-trace-analysis
    #rsync -rv --update --include='*/' --include='*.py' --exclude='*' /home/peter/disaggregation/fb-trace-analysis/* petergao@c33:/home/eecs/petergao/fb-trace-analysis
done
