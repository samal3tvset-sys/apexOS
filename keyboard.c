VGA_BUFFER = 0xB8000
VGA_WIDTH = 80
VGA_HEIGHT = 25

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

SCANCODE_MAP = {
    0x02: '1', 0x03: '2', 0x04: '3', 0x05: '4', 0x06: '5',
    0x07: '6', 0x08: '7', 0x09: '8', 0x0A: '9', 0x0B: '0',
    0x1E: 'a', 0x30: 'b', 0x2E: 'c', 0x20: 'd', 0x12: 'e',
    0x21: 'f', 0x22: 'g', 0x23: 'h', 0x17: 'i', 0x24: 'j',
    0x25: 'k', 0x26: 'l', 0x32: 'm', 0x31: 'n', 0x18: 'o',
    0x19: 'p', 0x10: 'q', 0x13: 'r', 0x1F: 's', 0x14: 't',
    0x16: 'u', 0x2F: 'v', 0x11: 'w', 0x2D: 'x', 0x15: 'y',
    0x2C: 'z', 0x39: ' '
}

def get_key():
    while not (inb(0x64) & 1):
        pass
    return inb(0x60)

def keyboard_main():
    clear_screen()
    print_string(0, 0, "Apex OS Keyboard Driver")
    print_string(2, 0, "Type something:")
    
    col = 0
    row = 4
    
    while True:
        scancode = get_key()
        if not (scancode & 0x80):
            if scancode in SCANCODE_MAP:
                char = SCANCODE_MAP[scancode]
                print_string(row, col, char)
                col += 1
                if col >= VGA_WIDTH:
                    col = 0
                    row += 1
        __asm__("hlt")

if __name__ == "__main__":
    keyboard_main()
