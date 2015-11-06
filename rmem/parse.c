#include <stdio.h>

typedef struct
{
        long timestamp;
        int page;
        int length;
	int count;
} __attribute__((packed)) access_record;



int main(int argc, char ** argv)
{
  if(argc != 3)
  {
    printf("parse input output\n");
    return -1;
  }
  FILE* dump;
  FILE *log;
  dump = fopen(argv[1], "rb");
  log = fopen(argv[2], "w");
  access_record rec;
 
  while(fread(&rec, 20, 1, dump))
  {
    fprintf(log, "%ld %d %d %d\n", rec.timestamp, rec.page, rec.length, rec.count);
  }
  fclose(log);
  fclose(dump);
  return 0;
}
