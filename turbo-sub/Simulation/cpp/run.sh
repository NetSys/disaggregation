ctrl_c()
{
  rm simulator$exptime
  echo "Done, results are in $fn"
  exit 0
}

trace_key="flow_trace: "
conf_file=$(cat $2 | grep $trace_key)
conf_file=${conf_file/flow_trace: /}


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
echo "======================FDist:======================" >> $fn
cat $conf_file >> $fn
cat $conf_file
echo ""
echo "======================Output:======================" >> $fn

make clean
cp simulator simulator$exptime

trap ctrl_c SIGINT
stdbuf -o0 ./simulator$exptime $@ | python tee.py $fn

ctrl_c



