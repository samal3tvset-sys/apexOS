VGA_BUFFER = 0xB8000
VGA_WIDTH = 80
VGA_HEIGHT = 25

def inb(port):
    val = 0
    __asm__ volatile("inb %1, %0" : "=a"(val) : "Nd"(port))
    return val

def outb(port, val):
    __asm__ volatile("outb %0, %1" : : "a"(val), "Nd"(port))

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

def wait_mouse(a_type):
    timeout = 100000
    if a_type == 0:
        while timeout > 0:
            if (inb(0x64) & 1):
                return
            timeout -= 1
    else:
        while timeout > 0:
            if not (inb(0x64) & 2):
                return
            timeout -= 1

def mouse_main():
    clear_screen()
    print_string(0, 0, "Apex OS PS/2 Mouse Driver")
    
    wait_mouse(1)
    outb(0x64, 0xA8)
    
    wait_mouse(1)
    outb(0x64, 0x20)
    wait_mouse(0)
    status = inb(0x60) | 2
    
    wait_mouse(1)
    outb(0x64, 0x60)
    wait_mouse(1)
    outb(0x60, status)
    
    wait_mouse(1)
    outb(0x64, 0xD4)
    wait_mouse(1)
    outb(0x60, 0xF4)
    
    x = 40
    y = 12
    print_string(y, x, "O")

    while True:
        if inb(0x64) & 1:
            packet = inb(0x60)
            print_string(2, 0, f"Packet: {packet:02X}")
        __asm__("hlt")

if __name__ == "__main__":
    mouse_main()
