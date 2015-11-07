#include <stdio.h>

typedef struct
{
        long timestamp;
        int page;
//        int length;
        int count;
} __attribute__((packed)) access_record;

#define RECORD_SIZE 16

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
 
  while(fread(&rec, RECORD_SIZE, 1, dump))
  {
    fprintf(log, "%ld %d %d %d\n", rec.timestamp, rec.page, 1, rec.count);
  }
  fclose(log);
  fclose(dump);
  return 0;
}
