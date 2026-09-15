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

void tasks_main(void) {
    clear_screen();
    
    print_string(2, 2, " Apex OS Task Manager ", 0x1F);
    print_string(4, 2, "PID   NAME             STATE     CPU", 0x0F);
    
    const char* tasks[] = {
        "-> 001   kernel_core      RUNNING   0.4%",
        "   002   vga_driver       WAITING   0.1%",
        "   003   memory_mgr       IDLE      0.0%",
        "   004   apex_shell       SLEEP     0.0%"
    };

    for (int i = 0; i < 4; i++) {
        print_string(6 + i, 4, tasks[i], (i == 0) ? VGA_HIGHLIGHT : 0x07);
    }

    while (1) {
        __asm__("hlt");
    }
}
