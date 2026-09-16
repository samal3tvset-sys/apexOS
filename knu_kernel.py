import sys
import time
import signal
import hashlib
import uuid
from enum import Enum
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Callable
from collections import defaultdict
import os

# ============================================================================
# ENUMS AND CONSTANTS
# ============================================================================

class ProcessState(Enum):
    """Process states"""
    NEW = 0
    READY = 1
    RUNNING = 2
    BLOCKED = 3
    ZOMBIE = 4
    TERMINATED = 5

class SignalType(Enum):
    """Signal types (Unix-like)"""
    SIGKILL = 9     # Kill (cannot be caught)
    SIGSTOP = 19    # Stop (cannot be caught)
    SIGTERM = 15    # Termination
    SIGINT = 2      # Interrupt (Ctrl-C)
    SIGSEGV = 11    # Segmentation violation
    SIGABRT = 6     # Abort
    SIGUSR1 = 10    # User-defined 1
    SIGUSR2 = 12    # User-defined 2

class VMPageState(Enum):
    """Virtual memory page states"""
    INVALID = 0
    VALID = 1
    DIRTY = 2
    SWAPPED = 3

class FileOpenMode(Enum):
    """File open modes"""
    READ = 1
    WRITE = 2
    READ_WRITE = 3
    APPEND = 4

class Colors:
    """Terminal colors"""
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    ENDC = '\033[0m'

# KNU Configuration
class KNUConfig:
    """KNU kernel configuration"""
    MAX_PROCESSES = 256
    MAX_THREADS = 1024
    MAX_FILES = 4096
    MAX_MEMORY = 4 * 1024 * 1024  # 4 MB
    PAGE_SIZE = 4096
    MAX_PAGES = MAX_MEMORY // PAGE_SIZE
    MAX_OPEN_FILES_PER_PROCESS = 64
    
    # Scheduler
    TIME_SLICE = 10  # ms
    PRIORITY_LEVELS = 10
    
    # IPC
    MAX_PIPES = 256
    MAX_MESSAGES = 1024
    
    # Device
    MAX_DEVICES = 32

# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class ProcessControlBlock:
    """Process Control Block (PCB)"""
    pid: int
    name: str
    state: ProcessState
    priority: int = 5
    entry_point: Optional[Callable] = None
    memory_start: int = 0
    memory_size: int = 0
    stack_pointer: int = 0
    instruction_pointer: int = 0
    creation_time: float = field(default_factory=time.time)
    runtime: int = 0
    signals: Dict[SignalType, Callable] = field(default_factory=dict)
    open_files: List['FileDescriptor'] = field(default_factory=list)
    parent_pid: Optional[int] = None
    children: List[int] = field(default_factory=list)
    exit_code: int = 0
    cpu_time: int = 0

@dataclass
class VMPage:
    """Virtual memory page"""
    page_num: int
    state: VMPageState
    physical_address: int
    dirty: bool = False
    accessed: bool = False
    protection: int = 3  # Read + Write + Execute

@dataclass
class FileDescriptor:
    """File descriptor"""
    fd: int
    path: str
    mode: FileOpenMode
    position: int = 0
    permissions: int = 0o644
    owner_pid: int = 0

@dataclass
class Pipe:
    """Inter-process pipe"""
    pipe_id: int
    reader_pid: int
    writer_pid: int
    buffer: bytes = b''
    max_size: int = 4096

@dataclass
class Message:
    """Message for IPC"""
    sender_pid: int
    receiver_pid: int
    msg_type: int
    data: bytes
    timestamp: float = field(default_factory=time.time)

@dataclass
class Device:
    """Device abstraction"""
    device_id: int
    name: str
    device_type: str  # 'block', 'char', 'net'
    read_fn: Optional[Callable] = None
    write_fn: Optional[Callable] = None

# ============================================================================
# KERNEL SUBSYSTEMS
# ============================================================================

class ProcessManager:
    """Process management subsystem"""
    
    def __init__(self):
        self.processes: Dict[int, ProcessControlBlock] = {}
        self.next_pid = 1
        self.current_pid = 0
        self.ready_queue: List[int] = []
        self.blocked_queue: List[int] = []
    
    def create_process(self, name: str, entry_point: Optional[Callable] = None,
                      priority: int = 5) -> Tuple[bool, int]:
        """Create new process"""
        if len(self.processes) >= KNUConfig.MAX_PROCESSES:
            return False, -1
        
        pid = self.next_pid
        self.next_pid += 1
        
        pcb = ProcessControlBlock(
            pid=pid,
            name=name,
            state=ProcessState.NEW,
            priority=priority,
            entry_point=entry_point,
            memory_size=64 * 1024,  # 64 KB per process
        )
        
        self.processes[pid] = pcb
        self.ready_queue.append(pid)
        
        return True, pid
    
    def terminate_process(self, pid: int) -> bool:
        """Terminate process"""
        if pid not in self.processes:
            return False
        
        pcb = self.processes[pid]
        
        # Close all open files
        for fd in pcb.open_files:
            pass  # File system will handle cleanup
        
        # Kill all children
        for child_pid in pcb.children:
            self.terminate_process(child_pid)
        
        pcb.state = ProcessState.TERMINATED
        return True
    
    def get_process(self, pid: int) -> Optional[ProcessControlBlock]:
        """Get process by PID"""
        return self.processes.get(pid)
    
    def list_processes(self) -> List[ProcessControlBlock]:
        """List all processes"""
        return list(self.processes.values())
    
    def schedule(self) -> Optional[int]:
        """Get next process to run (simple round-robin)"""
        if not self.ready_queue:
            return None
        
        # Move current to end
        if self.current_pid in self.ready_queue:
            self.ready_queue.remove(self.current_pid)
            self.ready_queue.append(self.current_pid)
        
        next_pid = self.ready_queue[0]
        self.current_pid = next_pid
        
        if next_pid in self.processes:
            self.processes[next_pid].state = ProcessState.RUNNING
        
        return next_pid

class VirtualMemoryManager:
    """Virtual memory management"""
    
    def __init__(self):
        self.page_table: Dict[int, VMPage] = {}
        self.free_pages: List[int] = list(range(KNUConfig.MAX_PAGES))
        self.page_map: Dict[int, int] = {}  # pid -> [page_nums]
    
    def allocate_pages(self, pid: int, num_pages: int) -> Tuple[bool, List[int]]:
        """Allocate pages for process"""
        if len(self.free_pages) < num_pages:
            return False, []
        
        allocated = []
        for _ in range(num_pages):
            if self.free_pages:
                page_num = self.free_pages.pop(0)
                page = VMPage(page_num=page_num, state=VMPageState.VALID,
                            physical_address=page_num * KNUConfig.PAGE_SIZE)
                self.page_table[page_num] = page
                allocated.append(page_num)
        
        self.page_map[pid] = allocated
        return True, allocated
    
    def free_pages(self, pid: int) -> bool:
        """Free pages of process"""
        if pid not in self.page_map:
            return False
        
        for page_num in self.page_map[pid]:
            if page_num in self.page_table:
                del self.page_table[page_num]
            self.free_pages.append(page_num)
        
        del self.page_map[pid]
        return True
    
    def get_stats(self) -> Dict:
        """Get memory statistics"""
        return {
            'total_memory': KNUConfig.MAX_MEMORY,
            'allocated_pages': KNUConfig.MAX_PAGES - len(self.free_pages),
            'free_pages': len(self.free_pages),
            'page_size': KNUConfig.PAGE_SIZE,
        }

class FileSystemAbstraction:
    """File system abstraction layer"""
    
    def __init__(self):
        self.files: Dict[str, Dict] = {}
        self.open_files: Dict[int, FileDescriptor] = {}
        self.next_fd = 3  # 0, 1, 2 are stdin, stdout, stderr
        self.inode_counter = 1
    
    def open_file(self, pid: int, path: str, mode: FileOpenMode) -> Tuple[bool, int]:
        """Open file"""
        if self.next_fd >= KNUConfig.MAX_FILES:
            return False, -1
        
        fd = self.next_fd
        self.next_fd += 1
        
        file_desc = FileDescriptor(
            fd=fd,
            path=path,
            mode=mode,
            owner_pid=pid
        )
        
        self.open_files[fd] = file_desc
        return True, fd
    
    def close_file(self, fd: int) -> bool:
        """Close file"""
        if fd in self.open_files:
            del self.open_files[fd]
            return True
        return False
    
    def read_file(self, fd: int, size: int) -> Tuple[bool, bytes]:
        """Read from file"""
        if fd not in self.open_files:
            return False, b''
        
        # Simulate file read
        return True, b'file_data'
    
    def write_file(self, fd: int, data: bytes) -> Tuple[bool, int]:
        """Write to file"""
        if fd not in self.open_files:
            return False, 0
        
        # Simulate file write
        return True, len(data)

class IPCManager:
    """Inter-Process Communication manager"""
    
    def __init__(self):
        self.pipes: Dict[int, Pipe] = {}
        self.messages: List[Message] = []
        self.next_pipe_id = 1
    
    def create_pipe(self, reader_pid: int, writer_pid: int) -> Tuple[bool, int]:
        """Create pipe"""
        pipe_id = self.next_pipe_id
        self.next_pipe_id += 1
        
        pipe = Pipe(
            pipe_id=pipe_id,
            reader_pid=reader_pid,
            writer_pid=writer_pid
        )
        
        self.pipes[pipe_id] = pipe
        return True, pipe_id
    
    def write_pipe(self, pipe_id: int, data: bytes) -> Tuple[bool, int]:
        """Write to pipe"""
        if pipe_id not in self.pipes:
            return False, 0
        
        pipe = self.pipes[pipe_id]
        if len(pipe.buffer) + len(data) > pipe.max_size:
            return False, 0
        
        pipe.buffer += data
        return True, len(data)
    
    def read_pipe(self, pipe_id: int, size: int) -> Tuple[bool, bytes]:
        """Read from pipe"""
        if pipe_id not in self.pipes:
            return False, b''
        
        pipe = self.pipes[pipe_id]
        data = pipe.buffer[:size]
        pipe.buffer = pipe.buffer[size:]
        
        return True, data
    
    def send_message(self, sender_pid: int, receiver_pid: int,
                    msg_type: int, data: bytes) -> bool:
        """Send message"""
        msg = Message(
            sender_pid=sender_pid,
            receiver_pid=receiver_pid,
            msg_type=msg_type,
            data=data
        )
        
        self.messages.append(msg)
        return True
    
    def recv_message(self, receiver_pid: int) -> Optional[Message]:
        """Receive message"""
        for i, msg in enumerate(self.messages):
            if msg.receiver_pid == receiver_pid:
                return self.messages.pop(i)
        return None

class SignalManager:
    """Signal handling"""
    
    def __init__(self, process_manager: ProcessManager):
        self.process_manager = process_manager
        self.default_handlers: Dict[SignalType, Callable] = {}
    
    def send_signal(self, pid: int, signal: SignalType) -> bool:
        """Send signal to process"""
        pcb = self.process_manager.get_process(pid)
        if not pcb:
            return False
        
        # Handle special signals
        if signal == SignalType.SIGKILL:
            self.process_manager.terminate_process(pid)
            return True
        
        # Call custom handler if exists
        if signal in pcb.signals:
            pcb.signals[signal]()
        
        return True
    
    def register_signal_handler(self, pid: int, signal: SignalType,
                               handler: Callable) -> bool:
        """Register signal handler"""
        pcb = self.process_manager.get_process(pid)
        if not pcb:
            return False
        
        pcb.signals[signal] = handler
        return True

class DeviceManager:
    """Device abstraction and management"""
    
    def __init__(self):
        self.devices: Dict[int, Device] = {}
        self.next_device_id = 1
    
    def register_device(self, name: str, device_type: str,
                       read_fn: Optional[Callable] = None,
                       write_fn: Optional[Callable] = None) -> Tuple[bool, int]:
        """Register device"""
        if self.next_device_id >= KNUConfig.MAX_DEVICES:
            return False, -1
        
        device_id = self.next_device_id
        self.next_device_id += 1
        
        device = Device(
            device_id=device_id,
            name=name,
            device_type=device_type,
            read_fn=read_fn,
            write_fn=write_fn
        )
        
        self.devices[device_id] = device
        return True, device_id
    
    def device_read(self, device_id: int, size: int) -> Tuple[bool, bytes]:
        """Read from device"""
        if device_id not in self.devices:
            return False, b''
        
        device = self.devices[device_id]
        if device.read_fn:
            return True, device.read_fn(size)
        
        return False, b''
    
    def device_write(self, device_id: int, data: bytes) -> Tuple[bool, int]:
        """Write to device"""
        if device_id not in self.devices:
            return False, 0
        
        device = self.devices[device_id]
        if device.write_fn:
            return True, device.write_fn(data)
        
        return False, 0
    
    def list_devices(self) -> List[Device]:
        """List all devices"""
        return list(self.devices.values())

# ============================================================================
# KNU KERNEL
# ============================================================================

class KNUKernel:
    """KNU Kernel - Main kernel class"""
    
    def __init__(self):
        self.boot_time = time.time()
        self.running = False
        self.process_manager = ProcessManager()
        self.memory_manager = VirtualMemoryManager()
        self.fs_manager = FileSystemAbstraction()
        self.ipc_manager = IPCManager()
        self.signal_manager = SignalManager(self.process_manager)
        self.device_manager = DeviceManager()
        self.kernel_uptime = 0
        self.system_calls = 0
    
    def kernel_boot(self):
        """Boot the kernel"""
        print(f"\n{Colors.BOLD}{Colors.CYAN}")
        print("╔════════════════════════════════════════╗")
        print("║                                        ║")
        print("║       KNU - K Not Unix v0.1            ║")
        print("║     Minimal Unix-like Kernel           ║")
        print("║      Based on OpenBSD Design           ║")
        print("║                                        ║")
        print("╚════════════════════════════════════════╝")
        print(f"{Colors.ENDC}\n")
        
        print(f"{Colors.BLUE}[KERNEL]{Colors.ENDC} Booting KNU kernel...\n")
        
        # Initialize kernel subsystems
        self._init_memory()
        self._init_filesystem()
        self._init_devices()
        self._init_processes()
        self._init_ipc()
        
        self.running = True
        
        print(f"{Colors.GREEN}[KERNEL] Kernel boot complete!{Colors.ENDC}\n")
    
    def _init_memory(self):
        """Initialize memory management"""
        print(f"  {Colors.GREEN}✓{Colors.ENDC} Memory manager initialized")
        stats = self.memory_manager.get_stats()
        print(f"    Total: {stats['total_memory'] // 1024} KB, Pages: {stats['allocated_pages']}")
    
    def _init_filesystem(self):
        """Initialize file system"""
        print(f"  {Colors.GREEN}✓{Colors.ENDC} File system initialized")
        print(f"    Standard descriptors: stdin(0), stdout(1), stderr(2)")
    
    def _init_devices(self):
        """Initialize device manager"""
        print(f"  {Colors.GREEN}✓{Colors.ENDC} Device manager initialized")
        
        # Register standard devices
        self.device_manager.register_device("console", "char")
        self.device_manager.register_device("null", "char")
        self.device_manager.register_device("zero", "char")
        
        print(f"    Devices: console, null, zero")
    
    def _init_processes(self):
        """Initialize process manager"""
        print(f"  {Colors.GREEN}✓{Colors.ENDC} Process manager initialized")
        
        # Create idle process
        success, pid = self.process_manager.create_process("idle")
        print(f"    Idle process (PID: {pid})")
        
        # Create init process
        success, pid = self.process_manager.create_process("init")
        print(f"    Init process (PID: {pid})")
    
    def _init_ipc(self):
        """Initialize IPC"""
        print(f"  {Colors.GREEN}✓{Colors.ENDC} IPC manager initialized")
        print(f"    Pipes and messages ready")
    
    def spawn_process(self, name: str, entry_point: Optional[Callable] = None,
                     priority: int = 5) -> Tuple[bool, int]:
        """Spawn new process"""
        success, pid = self.process_manager.create_process(name, entry_point, priority)
        
        if success:
            # Allocate memory for process
            self.memory_manager.allocate_pages(pid, 16)  # 64 KB = 16 pages
        
        return success, pid
    
    def syscall_handler(self, syscall_num: int, *args) -> any:
        """Handle system calls"""
        self.system_calls += 1
        
        syscalls = {
            1: self._syscall_write,
            2: self._syscall_read,
            3: self._syscall_open,
            4: self._syscall_close,
            5: self._syscall_fork,
            6: self._syscall_exec,
            7: self._syscall_exit,
            8: self._syscall_wait,
            9: self._syscall_pipe,
            10: self._syscall_getpid,
        }
        
        if syscall_num in syscalls:
            return syscalls[syscall_num](*args)
        
        return -1  # EINVAL
    
    def _syscall_write(self, fd: int, data: bytes) -> int:
        """write(2) system call"""
        if fd == 1:  # stdout
            print(data.decode(), end='')
            return len(data)
        
        success, written = self.fs_manager.write_file(fd, data)
        return written if success else -1
    
    def _syscall_read(self, fd: int, size: int) -> bytes:
        """read(2) system call"""
        success, data = self.fs_manager.read_file(fd, size)
        return data if success else b''
    
    def _syscall_open(self, path: str, mode: int) -> int:
        """open(2) system call"""
        success, fd = self.fs_manager.open_file(
            self.process_manager.current_pid,
            path,
            FileOpenMode(mode)
        )
        return fd if success else -1
    
    def _syscall_close(self, fd: int) -> int:
        """close(2) system call"""
        return 0 if self.fs_manager.close_file(fd) else -1
    
    def _syscall_fork(self) -> int:
        """fork(2) system call"""
        parent_pid = self.process_manager.current_pid
        success, child_pid = self.process_manager.create_process(f"fork_{parent_pid}")
        return child_pid if success else -1
    
    def _syscall_exec(self, path: str) -> int:
        """execve(2) system call"""
        # In real implementation, would load new process image
        return 0
    
    def _syscall_exit(self, code: int) -> None:
        """exit(2) system call"""
        pid = self.process_manager.current_pid
        self.process_manager.terminate_process(pid)
    
    def _syscall_wait(self, pid: int) -> int:
        """wait(2) system call"""
        # Simplified wait
        return 0
    
    def _syscall_pipe(self) -> Tuple[int, int]:
        """pipe(2) system call"""
        pid = self.process_manager.current_pid
        success, pipe_id = self.ipc_manager.create_pipe(pid, pid)
        return (pipe_id, pipe_id) if success else (-1, -1)
    
    def _syscall_getpid(self) -> int:
        """getpid(2) system call"""
        return self.process_manager.current_pid
    
    def get_kernel_stats(self) -> Dict:
        """Get kernel statistics"""
        uptime = time.time() - self.boot_time
        
        return {
            'uptime': uptime,
            'processes': len(self.process_manager.processes),
            'syscalls': self.system_calls,
            'memory': self.memory_manager.get_stats(),
            'devices': len(self.device_manager.devices),
        }
    
    def print_status(self):
        """Print kernel status"""
        print(f"\n{Colors.BOLD}{Colors.CYAN}=== KNU KERNEL STATUS ==={Colors.ENDC}\n")
        
        stats = self.get_kernel_stats()
        
        print(f"Uptime:        {stats['uptime']:.2f}s")
        print(f"Processes:     {stats['processes']}")
        print(f"Syscalls:      {stats['syscalls']}")
        print(f"Memory:")
        print(f"  Total:       {stats['memory']['total_memory'] // 1024} KB")
        print(f"  Allocated:   {stats['memory']['allocated_pages']} pages")
        print(f"  Free:        {stats['memory']['free_pages']} pages")
        print(f"Devices:       {stats['devices']}")
        
        print(f"\n{Colors.BOLD}Processes:{Colors.ENDC}")
        for proc in self.process_manager.list_processes():
            status_icon = {
                ProcessState.READY: "→",
                ProcessState.RUNNING: "▶",
                ProcessState.BLOCKED: "⏸",
                ProcessState.TERMINATED: "⏹",
            }.get(proc.state, "?")
            
            print(f"  {status_icon} PID {proc.pid:3d}: {proc.name:20s} [{proc.state.name}]")
        
        print(f"\n{Colors.BOLD}Devices:{Colors.ENDC}")
        for device in self.device_manager.list_devices():
            print(f"  {device.device_id}: {device.name:20s} ({device.device_type})")
        
        print()

# ============================================================================
# KNU SHELL (Simple command interpreter)
# ============================================================================

class KNUShell:
    """Simple KNU shell"""
    
    def __init__(self, kernel: KNUKernel):
        self.kernel = kernel
        self.running = True
    
    def run(self):
        """Run shell"""
        print(f"{Colors.BOLD}KNU Shell v0.1{Colors.ENDC}")
        print(f"Type 'help' for commands\n")
        
        while self.running:
            try:
                prompt = f"knu:/$ "
                cmd = input(Colors.CYAN + prompt + Colors.ENDC).strip()
                
                if not cmd:
                    continue
                
                self.execute_command(cmd)
            
            except KeyboardInterrupt:
                print(f"\n{Colors.YELLOW}[Shell] Interrupted{Colors.ENDC}")
            except EOFError:
                print(f"\n{Colors.GREEN}[Shell] Logout{Colors.ENDC}")
                break
            except Exception as e:
                print(f"{Colors.RED}Error: {e}{Colors.ENDC}")
    
    def execute_command(self, cmd: str):
        """Execute shell command"""
        parts = cmd.split()
        
        if not parts:
            return
        
        command = parts[0]
        args = parts[1:] if len(parts) > 1 else []
        
        commands = {
            'help': self.cmd_help,
            'status': self.cmd_status,
            'ps': self.cmd_ps,
            'spawn': self.cmd_spawn,
            'kill': self.cmd_kill,
            'devices': self.cmd_devices,
            'memory': self.cmd_memory,
            'syscall': self.cmd_syscall,
            'exit': self.cmd_exit,
        }
        
        if command in commands:
            commands[command](*args)
        else:
            print(f"{Colors.RED}Unknown command: {command}{Colors.ENDC}")
    
    def cmd_help(self, *args):
        """Help command"""
        print(f"""
{Colors.BOLD}KNU Commands:{Colors.ENDC}
  help      - Show this help
  status    - Show kernel status
  ps        - List processes
  spawn     - Spawn new process (spawn <name>)
  kill      - Kill process (kill <pid>)
  devices   - List devices
  memory    - Show memory stats
  syscall   - Test syscall (syscall <number> [args])
  exit      - Exit shell
        """)
    
    def cmd_status(self, *args):
        """Status command"""
        self.kernel.print_status()
    
    def cmd_ps(self, *args):
        """List processes"""
        print(f"\n{Colors.BOLD}Processes:{Colors.ENDC}\n")
        print(f"{'PID':>5} {'Name':<20} {'State':<12} {'Runtime':>8}")
        print("-" * 50)
        
        for proc in self.kernel.process_manager.list_processes():
            print(f"{proc.pid:>5} {proc.name:<20} {proc.state.name:<12} {proc.runtime:>8}ms")
        
        print()
    
    def cmd_spawn(self, *args):
        """Spawn process"""
        if not args:
            print(f"{Colors.RED}Usage: spawn <name>{Colors.ENDC}")
            return
        
        name = args[0]
        success, pid = self.kernel.spawn_process(name)
        
        if success:
            print(f"{Colors.GREEN}✓ Spawned process {name} (PID: {pid}){Colors.ENDC}")
        else:
            print(f"{Colors.RED}✗ Failed to spawn process{Colors.ENDC}")
    
    def cmd_kill(self, *args):
        """Kill process"""
        if not args:
            print(f"{Colors.RED}Usage: kill <pid>{Colors.ENDC}")
            return
        
        try:
            pid = int(args[0])
            success = self.kernel.process_manager.terminate_process(pid)
            
            if success:
                print(f"{Colors.GREEN}✓ Killed process {pid}{Colors.ENDC}")
            else:
                print(f"{Colors.RED}✗ Process not found{Colors.ENDC}")
        
        except ValueError:
            print(f"{Colors.RED}Invalid PID{Colors.ENDC}")
    
    def cmd_devices(self, *args):
        """List devices"""
        print(f"\n{Colors.BOLD}Devices:{Colors.ENDC}\n")
        print(f"{'ID':>3} {'Name':<20} {'Type':<10}")
        print("-" * 35)
        
        for device in self.kernel.device_manager.list_devices():
            print(f"{device.device_id:>3} {device.name:<20} {device.device_type:<10}")
        
        print()
    
    def cmd_memory(self, *args):
        """Show memory stats"""
        stats = self.kernel.memory_manager.get_stats()
        
        print(f"\n{Colors.BOLD}Memory Statistics:{Colors.ENDC}\n")
        print(f"Total Memory:     {stats['total_memory'] // 1024} KB")
        print(f"Page Size:        {stats['page_size']} bytes")
        print(f"Total Pages:      {KNUConfig.MAX_PAGES}")
        print(f"Allocated Pages:  {stats['allocated_pages']}")
        print(f"Free Pages:       {stats['free_pages']}")
        print(f"Usage:            {stats['allocated_pages'] * 100 // KNUConfig.MAX_PAGES}%\n")
    
    def cmd_syscall(self, *args):
        """Test syscall"""
        if not args:
            print(f"{Colors.RED}Usage: syscall <number> [args]{Colors.ENDC}")
            return
        
        try:
            syscall_num = int(args[0])
            result = self.kernel.syscall_handler(syscall_num)
            print(f"{Colors.GREEN}Syscall {syscall_num} returned: {result}{Colors.ENDC}")
        
        except (ValueError, IndexError):
            print(f"{Colors.RED}Invalid syscall number{Colors.ENDC}")
    
    def cmd_exit(self, *args):
        """Exit shell"""
        print(f"{Colors.YELLOW}[Shell] Exiting...{Colors.ENDC}")
        self.running = False

# ============================================================================
# MAIN
# ============================================================================

def main():
    """Main entry point"""
    kernel = KNUKernel()
    kernel.kernel_boot()
    
    shell = KNUShell(kernel)
    shell.run()
    
    print(f"\n{Colors.GREEN}KNU kernel shutdown.{Colors.ENDC}\n")

if __name__ == '__main__':
    main()