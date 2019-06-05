import docker
import json
import logging
import os
import redis
import socket
import subprocess
import time

from dx_agent.config import DEFAULT_CONFIG
from dx_agent.utils.fs_helper import ensure_dir

docker_client = docker.from_env()
logger = logging.getLogger('Container Manage')

"""
Stop containers: docker stop $(docker ps | grep python | grep -oP '^\w+')
"""


class ImageCommand:
    def __init__(self):
        self.dict = {
            'dx/python3': 'python3 -m dx_runtime'
        }

    def __getitem__(self, s):
        assert isinstance(s, str)
        key = s.split(':')[0]
        return self.dict[key]


image_to_command = ImageCommand()
redis_client = None
# redis_client = redis.Redis(
#     host=DEFAULT_CONFIG['redis_host'], port=DEFAULT_CONFIG['redis_port'])


def function_pullup(datas):
    result = {}
    for data in datas:
        logger.debug(data['runtime_id'])
        # NOTE: mark this as 'pending' in redis, key is runtime_id
        redis_client.set(f"{data['runtime_id']}:status", 'pending')
        name = data['name'].replace('function/', '')
        image = data['image']
        source = f"{data['source']}"
        function_path = os.path.join(
            DEFAULT_CONFIG['function_warehouse'], name)
        logger.info(f'function path at {function_path}')
        ensure_dir(function_path)
        # p = subprocess.run(
        #     ['wget', '-O', os.path.join(function_path, 'tmp.zip'), source], capture_output=True)
        # if p.returncode != 0:
        #     err = p.stderr.decode()
        #     err = err[0:min(200, len(err))]
        #     raise RuntimeError('wget error: {}'.format(err))
        # logger.debug(f'{p.returncode}\n{p.stdout}\n{p.stderr}')
        # if p.stderr:
        #     logger.error(p.stderr.decode())
        #     continue
        # logger.debug(' '.join(
        #     ['unzip', '-o', '-d', function_path, os.path.join(function_path, 'tmp.zip')]))
        # p = subprocess.run(['unzip', '-o', '-d', function_path,
        #                     os.path.join(function_path, 'tmp.zip')], capture_output=True)
        # logger.debug(p.stdout)
        # if p.returncode != 0:
        #     err = p.stderr.decode()
        #     err = err[0:min(200, len(err))]
        #     raise RuntimeError('unzip error: {}'.format(err))
        # logger.error(p.stderr.decode())
        # continue
        container = docker_client.containers.run(image,
                                                 # command=f"{image_to_command[image]} {data['entrypoint']}",
                                                 # 最小值为2
                                                 #  cpu_shares=data['cpu'] * 2,
                                                 cpu_quota=100000 * data['cpu'],
                                                 detach=True,
                                                 environment={
                                                     'RUNTIME_ID': data['runtime_id'],
                                                     'DX_RUNTIME': json.dumps(data),
                                                     'HOST_IP': socket.gethostbyname(socket.gethostname()),
                                                     'FOG_IP': os.getenv('MY_IP')
                                                 },
                                                 mem_limit=f"{data['memory']}b",
                                                 volumes={
                                                     function_path: {
                                                         'bind': '/data/function', 'mode': 'ro'
                                                     }
                                                 })
        result[data['runtime_id']] = container.id
        redis_client.mset({
            f"{data['runtime_id']}:container": container.id,
            f"{data['runtime_id']}:up_time": time.ctime(),
            f"{data['runtime_id']}:alive": 1,
            f"{data['runtime_id']}:visit_count": 0,
            f"{data['runtime_id']}:live_time": data['keepalive'] * 60
        })
        redis_client.expire(
            f"{data['runtime_id']}:alive", data['keepalive'] * 60)
    return result


container_command_table = {
    'function/pullup': function_pullup,
    'none/none': lambda: None
}


def init(redis_host, redis_port):
    global redis_client
    redis_client = redis.Redis(host=redis_host, port=redis_port)


def execute_command(cmd: str, data: list):
    if cmd not in container_command_table.keys():
        logger.error(f'command not found: {cmd}')
        raise RuntimeError(f'command {cmd} not found')
    else:
        return container_command_table[cmd](data)
