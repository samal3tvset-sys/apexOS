#define SECTOR_SIZE 512
#define MAX_FILES 16
#define FILENAME_MAX_LEN 32

struct FileEntry {
    char name[FILENAME_MAX_LEN];
    unsigned int start_sector;
    unsigned int size;
    unsigned char is_used;
};

struct FileSystem {
    struct FileEntry files[MAX_FILES];
    unsigned int total_sectors;
    unsigned int free_sector_ptr;
};

static struct FileSystem fs;

void fs_init() {
    fs.total_sectors = 2880;
    fs.free_sector_ptr = 34;
    for (int i = 0; i < MAX_FILES; i++) {
        fs.files[i].is_used = 0;
        fs.files[i].size = 0;
        fs.files[i].start_sector = 0;
    }
}

int fs_create(const char* name, unsigned int size) {
    for (int i = 0; i < MAX_FILES; i++) {
        if (!fs.files[i].is_used) {
            fs.files[i].is_used = 1;
            fs.files[i].start_sector = fs.free_sector_ptr;
            fs.files[i].size = size;
            
            int j = 0;
            while (name[j] != '\0' && j < FILENAME_MAX_LEN - 1) {
                fs.files[i].name[j] = name[j];
                j++;
            }
            fs.files[i].name[j] = '\0';
            
            fs.free_sector_ptr += (size + SECTOR_SIZE - 1) / SECTOR_SIZE;
            return i;
        }
    }
    return -1;
}

int fs_find(const char* name) {
    for (int i = 0; i < MAX_FILES; i++) {
        if (fs.files[i].is_used) {
            int match = 1;
            for (int j = 0; j < FILENAME_MAX_LEN; j++) {
                if (fs.files[i].name[j] != name[j]) {
                    match = 0;
                    break;
                }
                if (name[j] == '\0') break;
            }
            if (match) return i;
        }
    }
    return -1;
}
