ASM = nasm
CC = gcc
LD = ld

CFLAGS = -m32 -ffreestanding -fno-pie -fno-stack-protector -nostdlib
LDFLAGS = -m elf_i386 -T linker.ld

all: apex.iso

boot.bin: bootloader.asm
	$(ASM) -f bin bootloader.asm -o boot.bin

kernel.o: kernel.c
	$(CC) $(CFLAGS) -c kernel.c -o kernel.o

apex.bin: boot.bin kernel.o
	$(LD) $(LDFLAGS) -o apex.bin kernel.o

apex.iso: boot.bin apex.bin
	mkdir -p iso/boot
	cat boot.bin apex.bin > iso/boot/apex.sys
	xorriso -as mkisofs -R -V "APEXOS" -b boot.bin -no-emul-boot -boot-load-size 4 -o apex.iso iso
	rm -rf iso

clean:
	rm -f boot.bin kernel.o apex.bin apex.iso
