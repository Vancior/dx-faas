import docker
import json
import os
import redis
import subprocess
import time

from ..config import DEFAULT_CONFIG
from .fs_helper import ensure_dir

docker_client = docker.from_env()


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
redis_client = redis.Redis(port=DEFAULT_CONFIG['redis_port'])


def function_pullup(datas):
    for data in datas:
        # TODO: mark this as 'pending' in redis, key is runtime_id
        redis_client.set(f"{data['runtime_id']}:status", 'pending')
        name = data['name'].replace('function/', '')
        image = data['image']
        source = f"{data['source']}/function.zip"
        function_path = os.path.join(
            DEFAULT_CONFIG['function_storage_path'], name)
        print('=' * 10)
        print(function_path)
        print('=' * 10)
        ensure_dir(function_path)
        # subprocess.run(['wget', '-N', f"-P {function_path}", source])
        # subprocess.run(['unzip', '-o', f"-d {function_path}", f"{function_path}/function.zip"])
        subprocess.run(['wget', '-N', '-P', function_path, source])
        subprocess.run(['unzip', '-o', '-d', function_path,
                        f"{function_path}/function.zip"])
        container = docker_client.containers.run(image,
                                                 # auto_remove=True,
                                                 command=f"{image_to_command[image]} {data['entrypoint']}",
                                                 cpu_shares=data['cpu'],
                                                 detach=True,
                                                 environment={
                                                     'RUNTIME_ID': data['runtime_id'],
                                                     'DX_RUNTIME': json.dumps(data)
                                                 },
                                                 mem_limit=f"{data['memory']}m",
                                                 # ports={
                                                 #     '80/tcp': '8001'
                                                 # },
                                                 #  stderr=True,
                                                 #  stdout=True,
                                                 #  stream=True,
                                                 tty=True, # for debugging
                                                 volumes={
                                                     function_path: {
                                                         'bind': '/data/function', 'mode': 'ro'
                                                     }
                                                 })
        print(container)
        # return container
        # container.logs()
        redis_client.mset({
            f"{data['runtime_id']}:container": container.id,
            f"{data['runtime_id']}:up_time": time.ctime(),
            f"{data['runtime_id']}:alive": 1,
            f"{data['runtime_id']}:visit_count": 0,
            f"{data['runtime_id']}:live_time": data['keepalive'] * 60
        })
        redis_client.expire(
            f"{data['runtime_id']}:alive", data['keepalive'] * 60)
        # container_inspect = docker_client.api.inspect_container(container.id)
        # ip = container_inspect['NetworkSettings']['IPAddress']
        # TODO: setup a scheduler to stop container
        # return container


container_command_table = {
    'function/pullup': function_pullup
}
