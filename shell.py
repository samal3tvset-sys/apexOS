VGA_BUFFER = 0xB8000
VGA_WIDTH = 80
VGA_HEIGHT = 25

def outb(port, val):
    __asm__ volatile("outb %0, %1" : : "a"(val), "Nd"(port))

def inb(port):
    val = 0
    __asm__ volatile("inb %1, %0" : "=a"(val) : "Nd"(port))
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

def get_key():
    while not (inb(0x64) & 1):
        pass
    return inb(0x60)

def shell_main():
    clear_screen()
    print_string(0, 0, "Apex OS Python v0.1")
    print_string(2, 0, "Commands: help, clear, reboot")
    print_string(4, 0, "apex:/# ")

    while True:
        scancode = get_key()
        if scancode == 0x1C:
            print_string(6, 0, "Unknown command! Type 'help'")
        __asm__("hlt")

if __name__ == "__main__":
    shell_main()
