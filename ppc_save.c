#include <stdio.h>
#include <sys/mman.h>
#include <fcntl.h>
#include <sys/stat.h>
#include <stdlib.h>

#define FPGA_LOC "/dev/roach/mem"

#define PAGE_SIZE 4096

FILE *fp; //para modificarlo creo que tengo que hacer otro puntero...


int read_bram(int start, int end, FILE *fp, int fpga_fd){
	size_t length = 4096;
	off_t offset = 4096*PAGE_SIZE;
	int prot = (PROT_READ | PROT_WRITE);
	int flags = MAP_SHARED;
	void *addr;
	long long readval = 0;
	int internal_off = 0;
	size_t write;

	offset = (start/PAGE_SIZE)*PAGE_SIZE;
	internal_off = start%PAGE_SIZE;
	length = ((end-start)/PAGE_SIZE+1)*PAGE_SIZE;
	//printf("offset = %lu \n", offset);
	//printf("internal offset = %i \n", internal_off);
	//printf("length = %i\n", length);
	
	addr = mmap(NULL, length, prot, flags, fpga_fd, offset);
	readval = *((long long *)(addr+internal_off));
	//printf("1st value %llu \n",readval);

		//fwrite((addr+internal_off), length, length/8, fp);
	write = fwrite((addr+internal_off), 1024, 320, fp);  //esta raro esto...solo escribe 1024Bytes, arriba de eso caga
	//printf("data written! \n");
	printf("elements written %i \n", write);
	munmap(addr, length);
	return 1;
	
}



int main(int argc, char *argv[]){
	int iter;
	int counter;
	
	//hay que colocar las direcciones adecuadas
	//arreglo tema de direcciones para leer de una 

	int save0_init= 0x01000000;
	int save0_end = 0x0104FFFF;
	int save1_init= 0x010A0000;
	int save1_end =	0x010EFFFF;  //ahora los tamanos son iguales :)


	int full_mem0_i = 0x01180500;
	int full_mem0_e = 0x011805FF;
	int full_mem1_i = 0x01180600;
	int full_mem1_e = 0x011806FF;

	int read_data0 = 0x11C0100;
	int read_data1 = 0x11C0200;
	
	int fpga_fd = -1;
	size_t length = 4096;
	off_t offset = 4096*PAGE_SIZE;
	int internal_off = 0;
	int prot = (PROT_READ | PROT_WRITE);
	int flags = MAP_SHARED;
	void *addr;
	int read_val0=0;
	int read_val1=0;



	if(argc<2){
		printf("you have to enter the number of iterations..\n");
		return 1;
	}
	iter = atoi(argv[1]);
	printf("iter %i\n", iter);
	fp = fopen("save", "a");
	
	fpga_fd = open(FPGA_LOC, O_RDWR);
	if(fpga_fd == 0){
		printf("Error: couldnt open the registers file :(");
		return -1;
	}
	
	offset = (full_mem0_i/PAGE_SIZE)*PAGE_SIZE;
	internal_off = full_mem0_i%PAGE_SIZE;
	addr = mmap(NULL, length, prot, flags, fpga_fd, offset);
	printf("offset = %lu \n", offset);
	printf("intern off = %i \n", internal_off);		
	//falta iniciar la prueba ojala hacerlo con kcpcmd no mas
	system("/bin/kcpcmd -i -p 1 wordwrite rst_save 0 1");		
	system("/bin/kcpcmd -i -p 1 wordwrite reading_data0 0 0");
	system("/bin/kcpcmd -i -p 1 wordwrite reading_data1 0 0");
	system("/bin/kcpcmd -i -p 1 wordwrite rst_save 0 0");
	int i = 0;
	printf("full mem1 ");
	system("/bin/kcpcmd -x -p 2 read full_mem1 0 4");
	printf("\n\n\n");
	while(i<iter){
		read_val0 = *((int *)(addr+internal_off));  //read fullmem0 reg
		if(read_val0==1){
			munmap(addr, length);
			printf("reading 0\n");
			read_bram(save0_init, save0_end, fp, fpga_fd);
			system("/bin/kcpcmd -i -p 1 wordwrite reading_data0 0 1");
		    system("/bin/kcpcmd -i -p 1 wordwrite reading_data0 0 0");	
			addr = mmap(NULL, length, prot, flags, fpga_fd, offset);	
			}
		read_val1 = *((int *)(addr+256+internal_off));
		//printf("read val %i \n", read_val1);
		//system("/bin/kcpcmd -x -p 2 read full_mem1 0 4");
		if(read_val1==1){
            munmap(addr, length);
			printf("reading 1\n");
            read_bram(save1_init, save1_end, fp, fpga_fd);
			system("/bin/kcpcmd -i -p 1 wordwrite reading_data1 0 1");
		    system("/bin/kcpcmd -i -p 1 wordwrite reading_data1 0 0");
            addr = mmap(NULL, length, prot, flags, fpga_fd, offset);
			i ++;
            }
		
	}
	munmap(addr, length);
	fclose(fp);
	return 1;
}

