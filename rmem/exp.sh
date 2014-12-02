rmems=( 1500686 1762830 2024974 2287118 2549262 2614798 2680334 2745870 2811406 )

echo ============= >> exp_log.txt
for remote_mem in "${rmems[@]}"
do
  for i in {1..3}
  do
    echo "==========================rmem: $remote_mem iter: $i ===================="
    ./exit_rmem.sh
    ./exit_rmem.sh
    ./init_rmem.sh $remote_mem
    result=$(./get_bytes.sh)
    output="$(date) $remote_mem $result"
    echo $output
    echo $output >> exp_log.txt
  done
done
