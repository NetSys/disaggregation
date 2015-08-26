slave_id=0
while read slave; do
    echo "Slave=$slave, slave_id=$slave_id"
    ssh root@$slave "mkdir /mnt2/ycsb && /root/s3cmd/s3cmd get --recursive s3://succinct-datasets/ycsb/succinct/mc-${slave_id} /mnt2/ycsb" &
    slave_id=$((slave_id+1))
done < /root/spark/conf/slaves
wait
