ctrl_c()
{
  version=$(cat /proc/sys/fs/rmem/version)
  overflow=$(cat /proc/sys/fs/rmem/overflow)
  readbytes=$(cat /proc/sys/fs/rmem/read_bytes)
  writebytes=$(cat /proc/sys/fs/rmem/write_bytes)
  linecount=$(cat /proc/sys/fs/rmem/line_count)
  echo "version: $version    overflow: $overflow    readbytes: $readbytes    writebytes: $writebytes    linecount: $linecount"
  exit 0
}

trap ctrl_c SIGINT

echo 0 > /proc/sys/fs/rmem/overflow
echo 0 > /proc/sys/fs/rmem/read_bytes
echo 0 > /proc/sys/fs/rmem/write_bytes
echo 0 > /proc/sys/fs/rmem/line_count

num=2
count=0
cd /root/hadoop-2.5.1
./wordcount.sh $1 > /dev/null 2>&1 &
cd /root/disaggregation/rmem
sleep 30
while [ $count -le 10 ]
do
  num=$(ps aux | grep hadoop | wc -l)
  if [ $num -gt 1 ]
  then 
    count=0
  else
    count=$((count+1))
  fi
  sleep 1
done

sleep 5

ctrl_c
