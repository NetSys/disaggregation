a=( 7168 8192 9216 10240 )
for i in "${a[@]}"
do
  count=$((i*1024*1024/100))
  /root/hadoop-2.5.1/bin/hadoop jar /root/hadoop-2.5.1/share/hadoop/mapreduce/hadoop-mapreduce-examples-2.5.1.jar teragen $count /root/data/terasort/$i
  mv /root/data/terasort/$i/part-m-00000 /root/data/terasort/f$i.txt
  rm -r /root/data/terasort/$i
done
