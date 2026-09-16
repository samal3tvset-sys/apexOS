#include <stdint.h>

void vendor_init_hardware(void) {
    uint16_t port = 0xCF8;
    uint32_t data = 0x80000000;
    
    __asm__ volatile("outl %0, %1" : : "a"(data), "Nd"(port));
}

uint32_t vendor_read_pci(uint16_t bus, uint16_t device, uint16_t func, uint16_t offset) {
    uint32_t address = (1 << 31) | (bus << 16) | (device << 11) | (func << 8) | (offset & 0xfc);
    __asm__ volatile("outl %0, %1" : : "a"(address), "Nd"((uint16_t)0xCF8));
    uint32_t result;
    __asm__ volatile("inl %1, %0" : "=a"(result) : "Nd"((uint16_t)0xCFC));
    return result;
}
