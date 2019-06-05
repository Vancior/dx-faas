import argparse
import os
from dx_agent.config import DEFAULT_CONFIG
from dx_agent.utils.container_manage import init, execute_command
from dx_agent.utils.node_manage import node_manage_loop


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--redis-host', default='127.0.0.1')
    parser.add_argument('--redis-port', type=int, default=6379)
    parser.add_argument('--openresty-host', default='127.0.0.1')
    # parser.add_argument('--function-path', default='/data/functions')
    return parser.parse_args()


def _exec(cmd):
    key = f"{cmd['category']}/{cmd['action']}"
    return execute_command(key, cmd['data'])


def run():
    args = parse_args()
    init(args.redis_host, args.redis_port)
    os.environ['OPENRESTY_HOST'] = args.openresty_host
    # DEFAULT_CONFIG['redis_host'] = args.redis_host
    # DEFAULT_CONFIG['redis_port'] = args.redis_port
    node_manage_loop(DEFAULT_CONFIG['server_host'],
                     DEFAULT_CONFIG['server_port_node'], _exec)
