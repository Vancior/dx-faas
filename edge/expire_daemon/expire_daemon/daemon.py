import argparse
import docker
import logging
import os
import re
import redis
import traceback


def get_meta():
    redis_host = os.getenv('REDIS_HOST', '127.0.0.1')
    redis_port = os.getenv('REDIS_PORT', 6379)
    return {'redis_host': redis_host, 'redis_port': redis_port}


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--redis-host', default='127.0.0.1')
    parser.add_argument('--redis-port', type=int, default=6379)
    return parser.parse_args()


def run():
    # meta = get_meta()
    args = parse_args()

    docker_client = docker.from_env()
    redis_client = redis.Redis(
        host=args.redis_host, port=args.redis_port)

    pubsub = redis_client.pubsub()
    pubsub.subscribe('__keyevent@0__:expired')
    for msg in pubsub.listen():
        print(msg)
        if msg['type'] == 'message':
            match = re.match('(.*):alive', str(msg['data'], 'ascii'))
            if len(match.groups()) is not 1:
                print('error')
            else:
                runtime_id = match.groups()[0]
                redis_client.set(f"{runtime_id}:status", 'expire')
                try:
                    docker_id = str(redis_client.get(
                        f"{runtime_id}:container"), encoding='ascii')
                    if docker_id is not None:
                        docker_client.containers.get(docker_id).stop()
                    else:
                        logging.error(
                            f"{runtime_id} has no corresponding container")
                except docker.errors.NotFound as e:
                    print(e)
                    traceback.print_tb(e.__traceback__)
                except docker.errors.APIError as e:
                    print(e)
                    traceback.print_tb(e.__traceback__)
