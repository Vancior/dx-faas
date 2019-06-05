import logging
import msgpack
import socket
import socketserver
import threading

from .config import DEFAULT_CONFIG
from .service_register import ServiceRegister, ServiceRegisterError
from .utils.container_manage import container_command_table
from .utils.network import recvmsg

logger = logging.getLogger(__name__)

"""
如何解决服务器向边缘通信时的认证问题
"""


class MyHandler(socketserver.StreamRequestHandler):
    def handle(self):
        # data = msgpack.unpackb(bytes(self.rfile.readline().strip(), encoding='utf-8'), raw=False)
        # data = msgpack.unpackb(self.rfile.readline().strip(), raw=False)
        data = recvmsg(self.request)
        print(data)
        if data.get('category') is None or data.get('action') is None or data.get('data') is None:
            logger.error('receive invalid data: {}'.format(data))
            return
        key = '{}/{}'.format(data.get('category'), data.get('action'))
        if container_command_table.get(key) is None:
            logger.error('command not found: {}'.format(key))
            return
        container_command_table[key](data['data'])


def listen_server(server_addr):
    if DEFAULT_CONFIG['ipv6']:
        AF_INET = socket.AF_INET6
    else:
        AF_INET = socket.AF_INET
    try:
        with socket.socket(AF_INET, socket.SOCK_STREAM) as sock_listen:
            sock_listen.bind(('', DEFAULT_CONFIG['agent_recv_command_port']))
            sock_listen.listen()
            while True:
                sock_conn, address = sock_listen.accept()
                if address[0] != server_addr:
                    logging.warning('receive from invalid server {}'.format(address[0]))
                    sock_conn.close()
                    continue
                buf_list = []
                sock_conn.settimeout(100)
                while True:
                    buf = sock_conn.recv(4096)
                    if len(buf) > 0:
                        buf_list.append(buf)
                    else:
                        break
                data = msgpack.unpackb(b''.join(buf_list), raw=False)
                """ TODO: parse command """
                if data.get('category') is None or data.get('action') is None:
                    logging.warning('receive invalid data')
                    continue

    except Exception as e:
        raise e


def main():
    try:
        registration = ServiceRegister(server_addr=DEFAULT_CONFIG['server_address'])
        registration.register({'cpu': 2, 'memory': 8192})
        registration.heartbeat()
        print('after beat')
        cmd_server = socketserver.ThreadingTCPServer(('', DEFAULT_CONFIG['agent_recv_command_port']), MyHandler)
        cmd_server.serve_forever()
    except ServiceRegisterError as e:
        raise e
    except Exception as e:
        raise e


if __name__ == '__main__':
    main()
