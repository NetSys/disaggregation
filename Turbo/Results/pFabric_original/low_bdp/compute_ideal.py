import sys
sys.path.insert(0, '../..')
import numpy
#import plotter

import parse_ns2_trace as parse
import ideal as ideal

def main():
  f = open(sys.argv[1]).readlines()
  ideal_fct = ideal.get_ideal_fcts(f, 0, True)
  f2 = open(sys.argv[2], 'w')
  for x in ideal_fct:
    for y in x:
      f2.write(str(y) + " ")
    f2.write("\n")
  f2.close()


if __name__ == '__main__':
    main()

