#include <stdint.h>

extern "C" {
    uint32_t vendor_read_pci(uint16_t bus, uint16_t device, uint16_t func, uint16_t offset);
}

class SubvendorManager {
public:
    uint16_t get_subsystem_vendor(uint16_t bus, uint16_t device, uint16_t func) {
        uint32_t data = vendor_read_pci(bus, device, func, 0x2C);
        return static_cast<uint16_t>(data & 0xFFFF);
    }

    uint16_t get_subsystem_id(uint16_t bus, uint16_t device, uint16_t func) {
        uint32_t data = vendor_read_pci(bus, device, func, 0x2C);
        return static_cast<uint16_t>((data >> 16) & 0xFFFF);
    }
};

static SubvendorManager subvendor_mgr;

extern "C" uint16_t subvendor_get_id(uint16_t bus, uint16_t device, uint16_t func) {
    return subvendor_mgr.get_subsystem_id(bus, device, func);
}
