#include <stdint.h>

extern "C" {
    void terminal_print_string(const char* str);
    void cpu_halt(void);
}

void kernel_panic(const char* reason) {
    __asm__ volatile("cli");

    terminal_print_string("\nKERNEL PANIC: ");
    terminal_print_string(reason);
    terminal_print_string("\nSystem halted.\n");

    while (1) {
        __asm__ volatile("hlt");
    }
}
