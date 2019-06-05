import logging
import msgpack
import select
import socket
import struct

INF = 0x3f3f3f3f
DEFAULT_BUFFER_SIZE = 4096
DEFAULT_SOCKET_TIMEOUT = 5

logger = logging.getLogger('Agent Networking')


def packmsg(msg):
    msg_bytes = msgpack.packb(msg, use_bin_type=True)
    meta_bytes = struct.pack('>I', len(msg_bytes))
    return meta_bytes + msg_bytes


def recvmsg(sock, timeout=DEFAULT_SOCKET_TIMEOUT, buf_size=DEFAULT_BUFFER_SIZE):
    if timeout < 0:
        rlist, wlist, xlist = select.select([sock], [], [])
    else:
        rlist, wlist, xlist = select.select([sock], [], [], timeout)
    if len(rlist) == 0:
        raise socket.timeout('timeout when recv')
    buf_list = []
    total_len = INF
    read_len = 0
    sock.settimeout(DEFAULT_SOCKET_TIMEOUT)
    head = sock.recv(4)
    total_len = struct.unpack('>I', head)[0]
    logger.info(f'recv package length: {total_len}')
    while read_len < total_len:
        remain = total_len - read_len
        buf = sock.recv(min(remain, buf_size))
        if len(buf) == 0:
            break
        buf_list.append(buf)
        read_len += len(buf)
    return msgpack.unpackb(b''.join(buf_list), raw=False)


class TCPConnection:
    def __init__(self, host: str, port: int, timeout=DEFAULT_SOCKET_TIMEOUT):
        # NOTE just throw the error
        self.sock = socket.create_connection((host, port), timeout)

    def send(self, data: dict):
        self.sock.sendall(packmsg(data))

    def recv(self, timeout=DEFAULT_SOCKET_TIMEOUT, buf_size=DEFAULT_BUFFER_SIZE):
        return recvmsg(self.sock, timeout=timeout, buf_size=buf_size)
    
    def close(self):
        self.sock.close()


# REVIEW we don't have ca certificate for private ip, so we have to implement tcp encrypton ourselves.
# This can be done by mimic the TLS procedure
class SafeConnection:
    def __init__(self, hostname, port):
        pass
