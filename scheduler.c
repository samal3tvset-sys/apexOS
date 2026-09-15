class Task:
    def __init__(self, pid, name, state):
        self.pid = pid
        self.name = name
        self.state = state

VGA_BUFFER = 0xB8000
VGA_WIDTH = 80
VGA_HEIGHT = 25

tasks = [
    Task(0, "idle_task", "RUNNING"),
    Task(1, "shell_task", "READY"),
    Task(2, "vga_task", "WAITING")
]

current_task_idx = 0

def clear_screen():
    for i in range(0, VGA_WIDTH * VGA_HEIGHT * 2, 2):
        __asm__("movb $0x20, %%al\n\t"
                "movb $0x07, %%ah\n\t"
                "movw %%ax, %0" : : "m"(*(char*)(VGA_BUFFER + i)))

def print_string(row, col, text):
    offset = (row * VGA_WIDTH + col) * 2
    for i, char in enumerate(text):
        pos = VGA_BUFFER + offset + (i * 2)
        __asm__("movb %0, %%al\n\t"
                "movb $0x07, %%ah\n\t"
                "movw %%ax, %1" : : "r"(ord(char)), "m"(*(char*)pos))

def switch_task():
    global current_task_idx
    tasks[current_task_idx].state = "READY"
    current_task_idx = (current_task_idx + 1) % len(tasks)
    tasks[current_task_idx].state = "RUNNING"

def render_scheduler():
    clear_screen()
    print_string(0, 0, "Apex OS Preemptive Scheduler")
    for i, t in enumerate(tasks):
        line = f"PID {t.pid}: {t.name} [{t.state}]"
        print_string(2 + i, 0, line)

def scheduler_main():
    while True:
        switch_task()
        render_scheduler()
        __asm__("hlt")

if __name__ == "__main__":
    scheduler_main()
