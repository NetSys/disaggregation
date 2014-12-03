#rmems=( 1500686 1762830 2024974 2287118 2549262 2614798 2680334 2745870 2811406 )
rmems=( 2549262 )
input_size=( 64 128 256 512 1024 2048 3072 4096 5120 6144 )
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
      result=$(./get_bytes.sh $size)
      output="$(date) $remote_mem $size $result"
      echo $output
      echo $output >> exp_log.txt
    done
  done
done
