cd /root/disaggregation/rmem/
echo 0 > .app_running.tmp
if [ -a rmem_log.txt ]
then
  rm rmem_log.txt
fi

if [ -z "$(mount | grep /sys/kernel/debug)" ]
then
  mount -t debugfs debugfs /sys/kernel/debug
fi

if [ -a .disk_io.blktrace.0 ]
then 
  rm .disk_io.blktrace.0
fi

if [ -a .disk_io.blktrace.1 ]
then 
  rm .disk_io.blktrace.1
fi

echo "$(date +%y%m%d%H%M%S.%N)" > .metadata
blktrace -d /dev/xvda1 -o .disk_io &

count=0
while true; do
  cat /proc/rmem_log >> rmem_log.txt
  count=$((count+1))
  if [ $(( count % 10 )) -eq 0 ] && [ $(cat .app_running.tmp) -eq 1 ]; then
    break
  fi
done

killall -SIGINT blktrace


