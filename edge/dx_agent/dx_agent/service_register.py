import logging
import msgpack
import select
import socket
import socketserver
import threading
import time

from .config import DEFAULT_CONFIG
from .utils.network import TCPConnection

logger = logging.getLogger(__name__)

SERVER_UDP_LISTEN_PORT = 10001
SERVER_REGISTER_PORT = 10003
SERVER_HEARTBEAT_PORT = 10004
CLIENT_RECV_TIMEOUT = 5
CLIENT_RECV_PORT = 10002


class ServiceRegisterError(Exception):
    pass


class ServiceRegister:
    def __init__(self, server_addr=None, ipv6=DEFAULT_CONFIG['ipv6']):
        """ ipv6这些信息应该写进一个全局配置里 """
        self.ipv6 = ipv6
        if ipv6:
            self.AF_INET = socket.AF_INET6
        else:
            self.AF_INET = socket.AF_INET
        if server_addr is None:
            self.server_addr = self.broadcast_get_server()
        else:
            self.server_addr = server_addr
        logger.info('Server address: {}'.format(self.server_addr))
        self.heartbeat_thread = None
        self.heartbeat_flag = True

    def broadcast_get_server(self, service='schedule', socket_timeout=DEFAULT_CONFIG['socket_timeout'],
                             buf_size=DEFAULT_CONFIG['buf_size']):
        def send_broadcast():
            try:
                # udp socket
                with socket.socket(self.AF_INET, socket.SOCK_DGRAM) as sock_send:
                    # broadcast
                    sock_send.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                    msg = {'appid': 'sdlfkj345oijog0f9g', 'encrpyt': '98sdfjijf925iu5b345h'}
                    sock_send.snedto(msgpack.packb(msg, use_bin_type=True), ('<broadcast>', SERVER_UDP_LISTEN_PORT))
            except Exception as e:
                raise e

        try:
            # tcp socket
            with socket.socket(self.AF_INET, socket.SOCK_STREAM) as sock_recv:
                # listen
                sock_recv.bind(('', CLIENT_RECV_TIMEOUT))
                sock_recv.settimeout(socket_timeout)
                sock_recv.listen()

                send_broadcast()

                sock_conn, address = sock_recv.accept()
                try:
                    buf_list = []
                    sock_conn.settimeout(socket_timeout)
                    # sock_conn.setblocking(False)
                    # rlist, wlist, xlist = select.select([sock_conn], [], [], CLIENT_RECV_TIMEOUT)
                    # if len(rlist) is 0:
                    #     logger.error('receive from server timeout')
                    #     assert False
                    while True:
                        buf = sock_conn.recv(buf_size)
                        if len(buf) > 0:
                            buf_list.append(buf)
                        else:
                            break
                    data = msgpack.unpackb(b''.join(buf_list), raw=False)
                    result = data.get('service')
                    if result is None:
                        raise ServiceRegisterError('error when parsing message')
                    if result.lower() == service:
                        raise ServiceRegisterError('invalid server: expect {}, get {}'.format(service, result))
                    return address[0]
                except socket.timeout as e:
                    logger.error('connection timeout')
                    raise e
        except socket.timeout as e:
            logger.error('socket listen timeout')
            raise e
        except Exception as e:
            raise e

    def register(self, info):
        tcp_connection = TCPConnection(self.server_addr, SERVER_REGISTER_PORT, self.ipv6)
        tcp_connection.connect()
        tcp_connection.send(info)
        # tcp_connection.close()
        time.sleep(1)
        data = tcp_connection.receive()
        data = {'result': 'ok'}
        print(data)
        result = data.get('result')
        if result is None:
            raise ServiceRegisterError('error when parsing message')
        elif result != 'ok':
            raise ServiceRegisterError(result)
        # tcp_connection.close()
        # try:
        #     with socket.socket(self.AF_INET, socket.SOCK_STREAM) as sock_register:
        #         sock_register.connect((self.server_addr, SERVER_REGISTER_PORT))
        #         sock_register.sendall(msgpack.packb(info, use_bin_type=True))
        #         total_buf = []
        #         rlist, _, _ = select.select([sock_register], [], [], CLIENT_RECV_TIMEOUT)
        #         if len(rlist) is 0:
        #             assert False
        #         while True:
        #             buf = sock_register.recv(4096)
        #             if len(buf) > 0:
        #                 total_buf.append(buf)
        #             else:
        #                 break
        #         data = msgpack.unpackb(b''.join(total_buf), raw=False)
        #         result = data.get('result')
        #         if result is None:
        #             raise ServiceRegisterError('error when parsing message')
        #         elif result != 'ok':
        #             raise ServiceRegisterError(result)
        # except socket.timeout as e:
        #     logger.error('register connect timeout')
        #     raise e
        # except Exception as e:
        #     raise e

    def heartbeat(self, interval=5):
        def _beat():
            while self.heartbeat_flag:
                try:
                    with socket.socket(self.AF_INET, socket.SOCK_DGRAM) as sock_heartbeat:
                        msg = 'still alive'
                        print(msg)
                        sock_heartbeat.sendto(msgpack.packb(msg, use_bin_type=True),
                                              (self.server_addr, SERVER_HEARTBEAT_PORT))
                except Exception as e:
                    logger.error('send heartbeat failed:', e)
                time.sleep(interval)
        if self.heartbeat_thread is not None:
            self.heartbeat_flag = False
            self.heartbeat_thread.join()
        self.heartbeat_flag = True
        self.heartbeat_thread = threading.Thread(target=_beat)
        self.heartbeat_thread.start()

    def stop_heartbeat(self):
        if self.heartbeat_thread is not None:
            self.heartbeat_flag = False
            self.heartbeat_thread.join()
        self.heartbeat_flag = True

    # def heartbeat(self, interval=5):
    #     def _beat():
    #         try:
    #             with socket.socket(self.AF_INET, socket.SOCK_DGRAM) as sock_heartbeat:
    #                 msg = 'still alive'
    #                 print(msg)
    #                 sock_heartbeat.sendto(msgpack.packb(msg, use_bin_type=True),
    #                                       (self.server_addr, SERVER_HEARTBEAT_PORT))
    #                 threading.Timer(interval, _beat).start()
    #         except Exception:
    #             logger.error('send heartbeat failed')
    #     threading.Timer(interval, _beat).start()
        # if self.heartbeat_timer is None:
        #     self.heartbeat_timer = threading.Timer(interval, _beat)
        # else:
        #     self.heartbeat_timer.cancel()
        # self.heartbeat_timer.start()
