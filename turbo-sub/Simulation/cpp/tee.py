import sys
import os

f = open(sys.argv[1], "a")
while True:
  line = sys.stdin.readline()
  if line == "":
    break
  sys.stdout.write("~" + line)
  f.write(line)
f.close()
