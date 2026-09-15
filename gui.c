VGA_BUFFER = 0xB8000
VGA_WIDTH = 80
VGA_HEIGHT = 25

def clear_screen():
    for i in range(0, VGA_WIDTH * VGA_HEIGHT * 2, 2):
        __asm__("movb $0x20, %%al\n\t"
                "movb $0x07, %%ah\n\t"
                "movw %%ax, %0" : : "m"(*(char*)(VGA_BUFFER + i)))

def print_string(row, col, text, color=0x07):
    offset = (row * VGA_WIDTH + col) * 2
    for i, char in enumerate(text):
        pos = VGA_BUFFER + offset + (i * 2)
        __asm__("movb %0, %%al\n\t"
                "movb %1, %%ah\n\t"
                "movw %%ax, %2" : : "r"(ord(char)), "r"(color), "m"(*(char*)pos))

def draw_box(start_row, start_col, height, width, title):
    for r in range(height):
        for c in range(width):
            char = ' '
            if r == 0 or r == height - 1:
                char = '-'
            elif c == 0 or c == width - 1:
                char = '|'
            
            if r == 0 and c == 0: char = '+'
            if r == 0 and c == width - 1: char = '+'
            if r == height - 1 and c == 0: char = '+'
            if r == height - 1 and c == width - 1: char = '+'
            
            print_string(start_row + r, start_col + c, char, 0x1F)
            
    if title:
        print_string(start_row, start_col + 2, f"[{title}]", 0x1E)

def gui_main():
    clear_screen()
    
    for c in range(VGA_WIDTH):
        print_string(0, c, " ", 0x3F)
    print_string(0, 1, "Apex OS GUI", 0x3F)
    print_string(0, 70, "12:00", 0x3F)
    
    draw_box(3, 2, 10, 30, "System Monitor")
    print_string(4, 4, "CPU: 0.1%")
    print_string(5, 4, "RAM: 64MB / 1024MB")
    print_string(6, 4, "Uptime: 00:01:20")
    
    draw_box(3, 35, 10, 42, "Terminal")
    print_string(4, 37, "apex:/# gui running")
    print_string(5, 37, "apex:/# _")

    for c in range(VGA_WIDTH):
        print_string(VGA_HEIGHT - 1, c, " ", 0x70)
    print_string(VGA_HEIGHT - 1, 2, "Start", 0x71)

    while True:
        __asm__("hlt")

if __name__ == "__main__":
    gui_main()
