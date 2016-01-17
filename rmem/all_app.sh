for app in wordcount wordcount-hadoop terasort terasort-spark graphlab memcached memcached-local bdb timely
do
  echo "~~~~~~~~app $app~~~~~~~"
  echo "~~~~~~~~~~~~~~~~clearing data~~~~~~~~~~~~~~~~"
  python execute.py --task clear-all-data
  echo "~~~~~~~~~~~~~~~~preparing input data~~~~~~~~~~~~~~~~"
  python execute.py --task $app-prepare
  echo "~~~~~~~~~~~~~~~~running app~~~~~~~~~~~~~~~~"
  python execute.py --task $app --dstat
done
