cd /root/disaggregation/rmem/
echo 0 > .app_running.tmp
if [ -a rmem_log.txt ]
then
  rm rmem_log.txt
fi

count=0
while true; do
  cat /proc/rmem_log >> rmem_log.txt
  count=$((count+1))
  if [ $(( count % 10 )) -eq 0 ] && [ $(cat .app_running.tmp) -eq 1 ]; then
    break
  fi
done


