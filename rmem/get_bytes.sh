
ctrl_c()
{
  version=$(cat /proc/sys/fs/rmem/version)
  overflow=$(cat /proc/sys/fs/rmem/overflow)
  read_bytes=$(cat /proc/sys/fs/rmem/read_bytes)
  write_bytes=$(cat /proc/sys/fs/rmem/write_bytes)
  line_count=$(cat /proc/sys/fs/rmem/line_count)
  reduce_read=$((read_bytes-map_read))
  reduce_write=$((write_bytes-map_write))
  echo "ver: $version    of: $overflow    mapr: $map_read    mapw: $map_write    redr: $reduce_read    redw: $reduce_write    redstart: $map_done_at    linecount: $line_count"
  exit 0
}

trap ctrl_c SIGINT

echo 0 > /proc/sys/fs/rmem/overflow
echo 0 > /proc/sys/fs/rmem/read_bytes
echo 0 > /proc/sys/fs/rmem/write_bytes
echo 0 > /proc/sys/fs/rmem/line_count

num=2
count=0
#./wordcount.sh $1 > /dev/null 2>&1 &
./wordcount.sh $1 2>&1 | python hadoop_state.py &
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
