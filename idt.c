struct IDTEntry {
    unsigned short offset_low;
    unsigned short selector;
    unsigned char zero;
    unsigned char type_attr;
    unsigned short offset_high;
} __attribute__((packed));

struct IDTPtr {
    unsigned short limit;
    unsigned int base;
} __attribute__((packed));

static struct IDTEntry idt[256];
static struct IDTPtr idtp;

extern void idt_load();

void idt_set_gate(unsigned char num, unsigned long base, unsigned short sel, unsigned char flags) {
    idt[num].offset_low = (base & 0xFFFF);
    idt[num].selector = sel;
    idt[num].zero = 0;
    idt[num].type_attr = flags;
    idt[num].offset_high = (base >> 16) & 0xFFFF;
}

void idt_init() {
    idtp.limit = (sizeof(struct IDTEntry) * 256) - 1;
    idtp.base = (unsigned int)&idt;
    
    __asm__ volatile("lidt (%0)" : : "r"(&idtp));
}
