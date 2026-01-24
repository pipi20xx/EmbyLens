import os
import pty
import struct
import fcntl
import termios
import signal
import asyncio
import paramiko
from app.utils.logger import logger

class TerminalService:
    def __init__(self):
        self.mode = 'local' # local or ssh
        self.fd = None      # for local
        self.child_pid = None # for local
        
        self.ssh_client = None # for ssh
        self.channel = None    # for ssh

    async def connect_ssh(self, host_info: dict):
        """连接远程 SSH"""
        self.mode = 'ssh'
        try:
            self.ssh_client = paramiko.SSHClient()
            self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # 处理认证方式
            pkey = None
            if host_info.get('auth_type') == 'key' and host_info.get('private_key'):
                from io import StringIO
                pkey = paramiko.RSAKey.from_private_key(
                    StringIO(host_info['private_key']),
                    password=host_info.get('private_key_password')
                )

            # 运行在线程池中避免阻塞
            await asyncio.to_thread(
                self.ssh_client.connect,
                hostname=host_info['host'],
                port=int(host_info.get('port', 22)),
                username=host_info.get('username', 'root'),
                password=host_info.get('password'),
                pkey=pkey,
                timeout=10,
                banner_timeout=10
            )
            
            self.channel = self.ssh_client.invoke_shell(
                term='xterm-256color',
                width=120,
                height=40
            )
            # 设置非阻塞
            self.channel.setblocking(0)
            logger.info(f"[Terminal] SSH connected to {host_info['host']}")
            return True
        except Exception as e:
            logger.error(f"[Terminal] SSH connection failed: {e}")
            self.close()
            raise e

    def open_terminal(self, command=["/bin/bash"]):
        """启动本地伪终端"""
        self.mode = 'local'
        pid, fd = pty.fork()
        
        if pid == 0:  # 子进程
            os.environ['TERM'] = 'xterm-256color'
            os.environ['LANG'] = 'en_US.UTF-8'
            try:
                os.execvp(command[0], command)
            except Exception:
                os._exit(1)
        else:  # 父进程
            self.child_pid = pid
            self.fd = fd
            # 设置为非阻塞模式
            flags = fcntl.fcntl(self.fd, fcntl.F_GETFL)
            fcntl.fcntl(self.fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)
            logger.info(f"[Terminal] Local PTY started PID {pid}")
            return fd

    def read_output(self, max_bytes=1024 * 16):
        """统一读取接口"""
        if self.mode == 'local':
            if self.fd is None: return None
            try:
                return os.read(self.fd, max_bytes)
            except (BlockingIOError, IOError, OSError):
                return None
        elif self.mode == 'ssh':
            if self.channel is None or self.channel.closed: return None
            try:
                if self.channel.recv_ready():
                    return self.channel.recv(max_bytes)
            except Exception:
                pass
            return None
        return None

    def write_input(self, data: str):
        """统一写入接口"""
        if self.mode == 'local' and self.fd:
            try:
                os.write(self.fd, data.encode('utf-8'))
            except Exception as e:
                logger.error(f"Write error: {e}")
        elif self.mode == 'ssh' and self.channel:
            try:
                self.channel.send(data)
            except Exception as e:
                logger.error(f"SSH send error: {e}")

    def resize(self, rows: int, cols: int):
        """统一调整窗口大小"""
        if self.mode == 'local' and self.fd:
            try:
                s = struct.pack('HHHH', rows, cols, 0, 0)
                fcntl.ioctl(self.fd, termios.TIOCSWINSZ, s)
            except: pass
        elif self.mode == 'ssh' and self.channel:
            try:
                self.channel.resize_pty(width=cols, height=rows)
            except: pass

    def close(self):
        """统一清理资源"""
        if self.mode == 'local':
            if self.child_pid:
                try: os.kill(self.child_pid, signal.SIGHUP)
                except: pass
            if self.fd:
                try: os.close(self.fd)
                except: pass
                self.fd = None
        elif self.mode == 'ssh':
            if self.channel:
                try: self.channel.close()
                except: pass
            if self.ssh_client:
                try: self.ssh_client.close()
                except: pass