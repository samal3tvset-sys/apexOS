VGA_BUFFER = 0xB8000
VGA_WIDTH = 80
VGA_HEIGHT = 25

def outl(port, val):
    __asm__ volatile("outl %0, %1" : : "a"(val), "Nd"(port))

def inl(port):
    val = 0
    __asm__ volatile("inl %1, %0" : "=a"(val) : "Nd"(port))
    return val

def clear_screen():
    for i in range(0, VGA_WIDTH * VGA_HEIGHT * 2, 2):
        __asm__("movb $0x20, %%al\n\t"
                "movb $0x07, %%ah\n\t"
                "movw %%ax, %0" : : "m"(*(char*)(VGA_BUFFER + i)))

def print_string(row, col, text):
    offset = (row * VGA_WIDTH + col) * 2
    for i, char in enumerate(text):
        pos = VGA_BUFFER + offset + (i * 2)
        __asm__("movb %0, %%al\n\t"
                "movb $0x07, %%ah\n\t"
                "movw %%ax, %1" : : "r"(ord(char)), "m"(*(char*)pos))

def wifi_main():
    clear_screen()
    print_string(0, 0, "Apex OS Wi-Fi Driver")
    
    outl(0xCF8, 0x80000000 | (0 << 16) | (3 << 11) | (0 << 8))
    vendor = inl(0xCFC) & 0xFFFF
    
    if vendor != 0xFFFF:
        print_string(2, 0, "Wireless controller found!")
    else:
        print_string(2, 0, "No Wi-Fi hardware detected.")

    while True:
        __asm__("hlt")

if __name__ == "__main__":
    wifi_main()
