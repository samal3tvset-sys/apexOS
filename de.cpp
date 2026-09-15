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

void de_main(void) {
    clear_screen();
    
    print_string(2, 2, " Apex OS Desktop Environment ", 0x1F);
    print_string(4, 2, "ApexDE Window Manager v0.1", 0x0F);
    
    const char* elements[] = {
        "-> Apex Panel [Top Bar]",
        "   Terminal Emulator",
        "   System Monitor",
        "   ApexDE Settings"
    };

    for (int i = 0; i < 4; i++) {
        print_string(6 + i, 4, elements[i], (i == 0) ? VGA_HIGHLIGHT : 0x07);
    }

    while (1) {
        __asm__("hlt");
    }
}
