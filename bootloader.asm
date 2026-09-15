[org 0x7C00]
[bits 16]

start:
    cli
    xor ax, ax
    mov ds, ax
    mov es, ax
    mov ss, ax
    mov sp, 0x7C00
    sti

    mov si, boot_msg
    call print_string

    mov ah, 0x02
    mov al, 4
    mov ch, 0
    mov cl, 2
    mov dh, 0
    mov dl, 0x00
    mov bx, 0x1000
    int 0x13
    jc disk_error

    jmp 0x0000:0x1000

print_string:
    lodsb
    or al, al
    jz .done
    mov ah, 0x0E
    int 0x10
    jmp print_string
.done:
    ret

disk_error:
    mov si, err_msg
    call print_string

hang:
    cli
    hlt
    jmp hang

boot_msg db 'Apex OS: Loading in Real Mode...', 13, 10, 0
err_msg  db 'Disk read error!', 0

times 510-($-$$) db 0
dw 0xAA55
