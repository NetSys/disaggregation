#include <stdio.h>


typedef struct
{
        long timestamp;
        int page;
        int length;
        int batch;
} __attribute__((packed)) access_record;

#define RECORD_SIZE 20

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
    fprintf(log, "%d %ld %d %d\n", rec.batch, rec.timestamp, rec.page, rec.length);
  }
  fclose(log);
  fclose(dump);
  return 0;
}
