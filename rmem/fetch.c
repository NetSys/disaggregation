#include <stdio.h>
#include<signal.h>
#include<unistd.h>

FILE* dump;
int stop = 0;

void sig_handler(int signo)
{
  if (!stop && signo == SIGINT){
    printf("received SIGINT\n");
    stop = 1;
  }
}


int main(int argc, char ** argv)
{
  if(argc != 3)
  {
    printf("fetch input output\n");
    return -1;
  }
  if (signal(SIGINT, sig_handler) == SIG_ERR)
  {
    printf("\ncan't catch SIGINT\n");
    return -1;
  }
  FILE *fp;
  char rec[20];
  dump = fopen(argv[2], "w");
  while(!stop){
    fp = fopen(argv[1], "rb");
    while(fread(&rec, 20, 1, fp))
    {
      fwrite(&rec, 20, 1, dump);
      //printf("%ld %d %d %d\n", rec.timestamp, rec.page, rec.length, rec.count);
    }
    fclose(fp);
    fp = NULL;
  }
  fclose(dump);
  return 0;
}
