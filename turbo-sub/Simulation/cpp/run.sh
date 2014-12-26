ctrl_c()
{
  rm simulator$exptime
  echo "Done, results are in $fn"
  exit 0
}


exptime=$(date +%y%m%d%H%M%S)
fn=results/$exptime-$(hostname).txt
echo "Please input comment:"
read comment
echo "======================Cmd:======================" > $fn
echo $@ >> $fn
echo "======================Comment:======================" >> $fn
echo $comment >> $fn
echo "======================Config:======================" >> $fn
cat $2 >> $fn
echo "" >> $fn
echo "======================Output:======================" >> $fn

make clean
cp simulator simulator$exptime

trap ctrl_c SIGINT
stdbuf -o0 ./simulator$exptime $@ | tee -a $fn

ctrl_c



