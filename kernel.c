#define VGA_BUFFER ((volatile char*)0xB8000)
#define VGA_WIDTH 80
#define VGA_HEIGHT 25

unsigned char inb(unsigned short port) {
    unsigned char ret;
    __asm__ volatile("inb %1, %0" : "=a"(ret) : "Nd"(port));
    return ret;
}

void clear_screen() {
    for (int i = 0; i < VGA_WIDTH * VGA_HEIGHT * 2; i += 2) {
        VGA_BUFFER[i] = ' ';
        VGA_BUFFER[i + 1] = 0x07;
    }
}

void print_string(int row, int col, const char* str, char color) {
    int offset = (row * VGA_WIDTH + col) * 2;
    for (int i = 0; str[i] != '\0'; i++) {
        VGA_BUFFER[offset + (i * 2)] = str[i];
        VGA_BUFFER[offset + (i * 2) + 1] = color;
    }
}

extern void idt_init();
extern void fs_init();

void kernel_main() {
    clear_screen();
    print_string(0, 0, "Apex OS v0.1 - Low-Level Core", 0x1F);
    
    idt_init();
    print_string(2, 2, "[OK] IDT Initialized", 0x0A);
    
    fs_init();
    print_string(4, 2, "[OK] File System Mounted", 0x0A);
    
    print_string(6, 2, "apex:/# ", 0x0F);

    while (1) {
        if (inb(0x64) & 1) {
            unsigned char scancode = inb(0x60);
            if (scancode == 0x1C) {
                print_string(8, 2, "Command executed.", 0x07);
            }
        }
        __asm__("hlt");
    }
}
