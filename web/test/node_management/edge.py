import psutil
import socket
import time

from utils import TCPConnection


def get_system_info():
    cpu_freq = psutil.cpu_freq()._asdict()
    cpu_freq['current'] = int(cpu_freq['current'])
    return {'cpu': {'count': psutil.cpu_count(), 'freq': cpu_freq},
            'memory': psutil.virtual_memory()._asdict()}


def get_running_info():
    pass


def main(host, port):
    connection = None
    while True:
        try:
            connection = TCPConnection(host, port)
            connection.send(get_system_info())
            recv_count = 5
            confirm = None
            while recv_count > 0:
                try:
                    confirm = connection.recv()
                    break
                except socket.timeout as e:
                    print(e)
                    print(
                        'recv server confirm timeout, close count: {}'.format(recv_count))
                    recv_count -= 1
            if confirm is None:
                raise socket.timeout('server no response')
            if confirm['status'] == 'success':
                print('successfully join into fog nodes')
                break
                # TODO start health check process
                # using subprocess.Popen(['python3', '-m', ''], shell=True, )
            else:
                print(confirm['info'])
        except Exception as e:
            print(repr(e))
            if connection is not None:
                connection.close()
            time.sleep(3)
    if connection is not None:
        connection.close()


if __name__ == '__main__':
    main('127.0.0.1', 7000)
