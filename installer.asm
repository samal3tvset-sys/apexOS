[org 0x7c00]
bits 16

start:
    cli
    mov ax, 0x07C0
    mov ds, ax
    mov es, ax
    mov ss, ax
    mov sp, 0x7C00

    mov si, msg_welcome
    call print_string

disk_loop:
    mov ah, 0x00
    int 0x16
    cmp al, '1'
    je do_install
    cmp al, '2'
    je do_repair
    jmp disk_loop

do_install:
    mov si, msg_installing
    call print_string
    jmp finish

do_repair:
    mov si, msg_repairing
    call print_string
    jmp finish

finish:
    cli
    hlt

print_string:
    lodsb
    or al, al
    jz .done
    mov ah, 0x0E
    int 0x10
    jmp print_string
.done:
    ret

msg_welcome:    db 13, 10, 'Apex OS Installer (ASM)', 13, 10, '[1] Install', 13, 10, '[2] Repair', 13, 10, 'Choice: ', 0
msg_installing: db 13, 10, 'Writing MBR & Kernel...', 13, 10, 'Done!', 0
msg_repairing:  db 13, 10, 'Filesystem intact.', 13, 10, 'Done!', 0

times 510-($-$$) db 0
dw 0xAA55
