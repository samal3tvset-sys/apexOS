[bits 32]
global isr_80_handler
extern syscall_dispatcher

isr_80_handler:
    push ds
    push es
    push fs
    push gs
    pushad

    mov ax, 0x10
    mov ds, ax
    mov es, ax
    mov fs, ax
    mov gs, ax

    push esp
    call syscall_dispatcher
    add esp, 4

    popad
    pop gs
    pop fs
    pop es
    pop ds
    iretd
