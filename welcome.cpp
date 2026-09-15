#define VGA_BUFFER ((volatile char*)0xB8000)
#define VGA_COLOR 0x0F

void print_string(int row, int col, const char* str) {
    int offset = (row * 80 + col) * 2;
    for (int i = 0; str[i] != '\0'; i++) {
        VGA_BUFFER[offset + (i * 2)] = str[i];
        VGA_BUFFER[offset + (i * 2) + 1] = VGA_COLOR;
    }
}

extern "C" void welcome_main() {
    const char* banner[] = {
        "    _                  ___  ____  ",
        "   / \\   _ __   _____ / _ \\/ ___| ",
        "  / _ \\ | '_ \\ / _ \\ V / | \\___ \\ ",
        " / ___ \\| |_) |  __/> <| |_| |___) |",
        "/_/   \\_\\ .__/ \\___/_/\\_\\\\___/|____/ ",
        "        |_|                          "
    };

    for (int i = 0; i < 6; i++) {
        print_string(2 + i, 15, banner[i]);
    }

    print_string(10, 25, "Welcome to Apex OS v0.1");
    print_string(12, 22, "Press any key to enter shell...");

    while (1) {
        __asm__("hlt");
    }
}
