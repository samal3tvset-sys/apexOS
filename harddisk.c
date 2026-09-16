#include <stdint.h>

#define ATA_PRIMARY_DATA         0x1F0
#define ATA_PRIMARY_SECTOR_COUNT 0x1F2
#define ATA_PRIMARY_LBA_LOW      0x1F3
#define ATA_PRIMARY_LBA_MID      0x1F4
#define ATA_PRIMARY_LBA_HIGH     0x1F5
#define ATA_PRIMARY_DEVICE       0x1F6
#define ATA_PRIMARY_COMMAND      0x1F7
#define ATA_CMD_READ_PIO         0x20

void harddisk_read_sector(uint32_t lba, uint8_t* buffer) {
    __asm__ volatile("outb %0, %1" : : "a"((uint8_t)(1)), "Nd"((uint16_t)ATA_PRIMARY_SECTOR_COUNT));
    __asm__ volatile("outb %0, %1" : : "a"((uint8_t)(lba & 0xFF)), "Nd"((uint16_t)ATA_PRIMARY_LBA_LOW));
    __asm__ volatile("outb %0, %1" : : "a"((uint8_t)((lba >> 8) & 0xFF)), "Nd"((uint16_t)ATA_PRIMARY_LBA_MID));
    __asm__ volatile("outb %0, %1" : : "a"((uint8_t)((lba >> 16) & 0xFF)), "Nd"((uint16_t)ATA_PRIMARY_LBA_HIGH));
    __asm__ volatile("outb %0, %1" : : "a"((uint8_t)(0xE0 | ((lba >> 24) & 0x0F))), "Nd"((uint16_t)ATA_PRIMARY_DEVICE));
    __asm__ volatile("outb %0, %1" : : "a"((uint8_t)(ATA_CMD_READ_PIO)), "Nd"((uint16_t)ATA_PRIMARY_COMMAND));

    uint16_t* ptr = (uint16_t*)buffer;
    for (int i = 0; i < 256; i++) {
        uint16_t tmp;
        __asm__ volatile("inw %1, %0" : "=a"(tmp) : "Nd"((uint16_t)ATA_PRIMARY_DATA));
        ptr[i] = tmp;
    }
}
