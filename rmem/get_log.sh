ctrl_c()
{
  version=$(cat /proc/sys/fs/rmem/version)
  overflow=$(cat /proc/sys/fs/rmem/overflow)
  readbytes=$(cat /proc/sys/fs/rmem/read_bytes)
  writebytes=$(cat /proc/sys/fs/rmem/write_bytes)
  linecount=$(cat /proc/sys/fs/rmem/line_count)
  echo "version: $version    overflow: $overflow    readbytes:$readbytes    writebytes:$writebytes    linecount:$linecount"
  exit 0
}

trap ctrl_c SIGINT

rm rmem_log.txt
echo 0 > /proc/sys/fs/rmem/overflow
echo 0 > /proc/sys/fs/rmem/read_bytes
echo 0 > /proc/sys/fs/rmem/write_bytes
echo 0 > /proc/sys/fs/rmem/line_count
while true; do
	cat /proc/rmem_log >> rmem_log.txt
done

