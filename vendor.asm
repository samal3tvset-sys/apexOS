[bits 32]
global vendor_port_byte_in
global vendor_port_byte_out
global vendor_port_word_in
global vendor_port_word_out

vendor_port_byte_in:
    mov dx, [esp + 4]
    in al, dx
    ret

vendor_port_byte_out:
    mov dx, [esp + 4]
    mov al, [esp + 8]
    out dx, al
    ret

vendor_port_word_in:
    mov dx, [esp + 4]
    in ax, dx
    ret

vendor_port_word_out:
    mov dx, [esp + 4]
    mov ax, [esp + 8]
    out dx, ax
    ret
