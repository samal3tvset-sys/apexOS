__asm__(
    ".code16\n"
    ".global _start\n"
    "_start:\n"
    "cli\n"
    "xor ax, ax\n"
    "mov ds, ax\n"
    "mov es, ax\n"
    "mov ss, ax\n"
    "mov sp, 0x7C00\n"
    "sti\n"

    "mov ah, 0x02\n"
    "mov al, 15\n"
    "mov ch, 0\n"
    "mov cl, 2\n"
    "mov dh, 0\n"
    "mov dl, 0x00\n"
    "mov bx, 0x1000\n"
    "int 0x13\n"
    "jc disk_error\n"

    "cli\n"
    "lgdt (gdt_descriptor)\n"
    "mov eax, cr0\n"
    "or eax, 1\n"
    "mov cr0, eax\n"

    "ljmp $0x08, $protected_mode_start\n"

    "disk_error:\n"
    "cli\n"
    "hlt\n"

    ".code32\n"
    "protected_mode_start:\n"
    "mov ax, 0x10\n"
    "mov ds, ax\n"
    "mov es, ax\n"
    "mov fs, ax\n"
    "mov gs, ax\n"
    "mov ss, ax\n"
    "mov esp, 0x90000\n"

    "call loader_main\n"

    "hang_32:\n"
    "hlt\n"
    "jmp hang_32\n"

    "gdt_start:\n"
    ".quad 0\n"
    "gdt_code:\n"
    ".word 0xFFFF, 0x0000\n"
    ".byte 0x00, 0x9A, 0xCF, 0x00\n"
    "gdt_data:\n"
    ".word 0xFFFF, 0x0000\n"
    ".byte 0x00, 0x92, 0xCF, 0x00\n"
    "gdt_end:\n"

    "gdt_descriptor:\n"
    ".word gdt_end - gdt_start - 1\n"
    ".long gdt_start\n"
);

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

void loader_main(void) {
    clear_screen();
    
    print_string(2, 2, " Apex OS Bootloader ", 0x1F);
    print_string(4, 2, "Select boot option:", 0x0F);
    
    const char* items[] = {
        "-> Apex OS [Normal Mode]",
        "   Apex OS [Recovery Mode]",
        "   Reboot",
        "   Power Off"
    };

    for (int i = 0; i < 4; i++) {
        print_string(7 + i, 4, items[i], (i == 0) ? VGA_HIGHLIGHT : 0x07);
    }

    while (1) {
        __asm__("hlt");
    }
}

void __attribute__((section(".boot_sig"), used)) dummy() {
    __asm__(".org 510\n.word 0xAA55\n");
}
