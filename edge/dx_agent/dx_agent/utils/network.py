import logging
import msgpack
import select
import socket
import struct

from ..config import DEFAULT_CONFIG

INF = 0x3f3f3f3f


def packmsg(msg):
    msg_bytes = msgpack.packb(msg, use_bin_type=True)
    meta_bytes = struct.pack('>I', len(msg_bytes))
    return meta_bytes + msg_bytes


def recvmsg(sock, buf_size=DEFAULT_CONFIG['buf_size']):
    buf_list = []
    total_len = INF
    read_len = 0
    while read_len < total_len:
        buf = sock.recv(buf_size)
        if len(buf) == 0:
            break
        if len(buf_list) is 0:
            total_len = struct.unpack('>I', buf[0:4])[0]
            buf = buf[4:]
        buf_list.append(buf)
        read_len += len(buf)
    return msgpack.unpackb(b''.join(buf_list), raw=False)


class TCPConnection:
    def __init__(self, addr, port, ipv6=DEFAULT_CONFIG['ipv6']):
        self.addr = addr
        self.port = port
        self.sock = None
        if ipv6:
            self.AF_INET = socket.AF_INET6
        else:
            self.AF_INET = socket.AF_INET

    def connect(self, timeout=DEFAULT_CONFIG['socket_timeout']):
        try:
            if self.sock is not None:
                self.sock.close()
            else:
                self.sock = socket.socket(self.AF_INET, socket.SOCK_STREAM)
                self.sock.settimeout(timeout)
                self.sock.connect((self.addr, self.port))
        except socket.timeout as e:
            logging.error('socket timeout')
            raise e
        except Exception as e:
            raise e

    def send(self, msg):
        try:
            if self.sock is None:
                self.connect()
            self.sock.sendall(packmsg(msg))
            # self.sock.sendall(msgpack.packb(msg, use_bin_type=True))
        except BrokenPipeError as e:
            raise e

    def receive(self, timeout=DEFAULT_CONFIG['recv_timeout'], buf_size=DEFAULT_CONFIG['buf_size']):
        rlist, _, _ = select.select([self.sock], [], [], timeout)
        if len(rlist) is 0:
            logging.error('receive timeout')
            return None
        return recvmsg(self.sock)
        # buf_list = []
        # while True:
        #     buf = self.sock.recv(buf_size)
        #     if len(buf) > 0:
        #         buf_list.append(buf)
        #     if len(buf) < buf_size:
        #         break
        # data = msgpack.unpackb(b''.join(buf_list), raw=False)
        # return data

    def close(self):
        self.sock.close()
        self.sock = None
