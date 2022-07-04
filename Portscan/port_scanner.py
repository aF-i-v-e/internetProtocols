from queue import Queue
import socket
import ssl
from concurrent.futures import ThreadPoolExecutor
from _socket import timeout, getservbyport

message = b'a' * 250 + b'\r\n\r\n'


class PortScanner:
    def __init__(self, args):
        self.host = args.host
        self.left_port_border = args.ports[0]
        self.right_port_border = args.ports[1] + 1
        self.is_udp = args.u
        self.q = Queue()
        self.executor = ThreadPoolExecutor(3)

    def scan(self):
        for port in range(self.left_port_border, self.right_port_border):
            self.q.put(port)
        for port in range(self.left_port_border, self.right_port_border):
            if self.is_udp:
                future = self.executor.submit(self.udp_scan, q=self.q, port_type="UDP")
            else:
                future = self.executor.submit(self.tcp_scan, q=self.q, port_type="TCP")
            thread_result = future.result()
        self.q.join()
        print(f'All ports from the range {self.left_port_border}:{self.right_port_border - 1} have been successfully '
              f'scanned')

    def udp_scan(self, q, port_type: str):
        port = q.get()
        try:
            sock = socket.socket(socket.AF_INET,  # Internet
                                 socket.SOCK_DGRAM)  # UDP
            sock.settimeout(3)
            sock.sendto(message, (self.host, port))
            data, address = sock.recvfrom(4096)  # buffer size is 4096 bytes
            print(f'{port_type} {port} {PortScanner.define_answer_type(data, port, "udp")}')
        except (timeout, OSError):
            pass
        except PermissionError:
            print(f'UDP port: {port} Permission Error')
        finally:
            q.task_done()

    def tcp_scan(self, q, port_type: str):
        port = q.get()
        try:
            try:
                data = self.create_protected_connect(port)
            except (timeout, OSError):
                data = self.create_connect(port)
            print(f'{port_type} {port} {PortScanner.define_answer_type(data, port, "tcp")}')
        except (timeout, OSError):
            pass
        except (ConnectionRefusedError, timeout):
            pass
        except PermissionError:
            print(f'TCP port: {port} Permission Error')
        finally:
            q.task_done()

    def create_protected_connect(self, port):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)
        sock.connect((self.host, port))
        ssl_socket = ssl.wrap_socket(sock)
        ssl_socket.send(message)
        data = ssl_socket.recv(4096)
        return data

    def create_connect(self, port):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)
        sock.connect((self.host, port))
        sock.send(message)
        return sock.recv(4096)

    @staticmethod
    # NTP/DNS/SMTP/POP3/IMAP/HTTP
    def define_answer_type(data: bytes, port: int, transport: str):
        if len(data) > 4 and b'HTTP' in data:
            return 'HTTP'
        if b'SMTP' in data or b'EHLO' in data:
            return 'SMTP'
        if b'POP3' in data or data.startswith(b'+OK') or data.startswith(b'+'):
            return 'POP3'
        if b'IMAP' in data:
            return 'IMAP'
        try:
            return getservbyport(port, transport).upper()
        except OSError:
            return '-'
