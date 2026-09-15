#define VGA_BUFFER ((volatile char*)0xB8000)
#define VGA_COLOR 0x07
#define VGA_HIGHLIGHT 0x1F

void clear_screen() {
    for (int i = 0; i < 80 * 25 * 2; i += 2) {
        VGA_BUFFER[i] = ' ';
        VGA_BUFFER[i + 1] = 0x07;
    }
}

void print_string(int row, int col, const char* str, char color) {
    int offset = (row * 80 + col) * 2;
    for (int i = 0; str[i] != '\0'; i++) {
        VGA_BUFFER[offset + (i * 2)] = str[i];
        VGA_BUFFER[offset + (i * 2) + 1] = color;
    }
}

void graphics_main(void) {
    clear_screen();
    
    print_string(2, 2, " Apex OS Graphics Subsystem ", 0x1F);
    print_string(4, 2, "VGA Text Mode 80x25 Active", 0x0F);
    
    const char* info[] = {
        "-> Resolution: 80x25 characters",
        "   Color Depth: 16-color text attributes",
        "   Frame Buffer: 0xB8000",
        "   Status: Hardware Accelerated"
    };

    for (int i = 0; i < 4; i++) {
        print_string(6 + i, 4, info[i], (i == 0) ? VGA_HIGHLIGHT : 0x07);
    }

    while (1) {
        __asm__("hlt");
    }
}
