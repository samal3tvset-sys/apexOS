[bits 64]
global enter_long_mode
extern kernel_main

enter_long_mode:
    cli

    mov rax, cr4
    or rax, (1 << 5)
    mov cr4, rax

    mov rcx, 0xC0000080
    rdmsr
    or rax, (1 << 8)
    wrmsr

    mov rax, cr0
    or rax, (1 << 31) | (1 << 0)
    mov cr0, rax

    lgdt [rdi]

    jmp 0x08:kernel_main
