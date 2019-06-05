import concurrent.futures
import logging
import os
import psutil
import socket
import subprocess
import time

from dx_agent.utils.network import TCPConnection

logger = logging.getLogger('Node Manage')


def get_system_info():
    # logger.info(repr(psutil.cpu_freq()))
    # logger.info(repr(psutil.virtual_memory()))
    cpu_freq = psutil.cpu_freq()
    if cpu_freq is None:
        cpu_freq = {'current': 2000, 'min': 800, 'max': 2500}
    else:
        cpu_freq = cpu_freq._asdict()
    # cpu_freq = psutil.cpu_freq()._asdict()
    cpu_freq['current'] = int(cpu_freq['current'])
    mlimit = subprocess.run(
        ['cat', '/sys/fs/cgroup/memory/memory.limit_in_bytes'],
        capture_output=True)
    mused = subprocess.run(
        ['cat', '/sys/fs/cgroup/memory/memory.usage_in_bytes'],
        capture_output=True)
    return {
        'cpu': {
            'count': psutil.cpu_count(),
            'freq': cpu_freq
        },
        'memory': {
            'total': int(mlimit.stdout.decode()),
            'used': int(mused.stdout.decode())
        },
        # 'memory': psutil.virtual_memory()._asdict(), # this will report host spec because of procfs
        'ip': os.getenv('MY_IP'),
        'gateway': '127.0.0.1'
        # 'gateway': os.getenv('OPENRESTY_HOST')
    }
    # 'ip': socket.gethostbyname(socket.gethostname())}


def get_running_info():
    pass


def node_manage_loop(host, port, recv_cmd_callback):
    # cmd_executor = concurrent.futures.ThreadPoolExecutor(max_workers=5)
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
                    logger.error(
                        'recv server confirm timeout, close count: {}'.format(
                            recv_count))
                    recv_count -= 1
            if confirm is None:
                raise socket.timeout('server no response')
            if confirm['status'] == 'success':
                logger.info('successfully join into fog nodes')
                # TODO start health check process
                # using subprocess.Popen(['python3', '-m', ''], shell=True, )
                while True:
                    cmd = connection.recv(timeout=-1)
                    logger.info(repr(cmd))
                    # cmd_executor.submit(recv_cmd_callback, (cmd,))
                    try:
                        data = recv_cmd_callback(cmd)
                        connection.send({'status': 'success', 'data': data})
                    except Exception as e:
                        logger.error(e)
                        connection.send({'status': 'fail', 'info': repr(e)})
            else:
                raise RuntimeError(f"confirm failed: {confirm['info']}")
                # logger.error(f"confirm failed: {confirm['info']}")
        except Exception as e:
            logger.error(repr(e))
            logger.error('lose connection')
            if connection is not None:
                connection.close()
            time.sleep(3)
    if connection is not None:
        connection.close()
