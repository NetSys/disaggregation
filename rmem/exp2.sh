#rmems=( 1500686 1762830 2024974 2287118 2549262 2614798 2680334 2745870 2811406 )
rmems=( 2549262 )
input_size=( 20480 30720 )
#input_size=( 4096 )

echo ============= >> exp_log.txt
for remote_mem in "${rmems[@]}"
do
  for size in "${input_size[@]}"
  do
    for i in {1..3}
    do
      echo "==========================rmem: $remote_mem size: $size iter: $i ===================="
      ./exit_rmem.sh
      ./exit_rmem.sh
      ./init_rmem.sh $remote_mem
      result=$(./wordcount.sh $size 2>&1 | python hadoop_state.py)
      output="$(date +%y%m%d%H%M%S) $remote_mem $size $result"
      echo $output
      echo $output >> exp_log.txt
    done
  done
done
