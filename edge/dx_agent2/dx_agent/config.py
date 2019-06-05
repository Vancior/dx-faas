import configparser
import os


class AgentConfig(dict):
    def update(self, other):
        self_keys = self.keys()
        for k, v in other.items():
            k = k.lower()
            if k in self_keys:
                self[k] = type(self[k])(v)


GLOBAL_CONFIG = configparser.ConfigParser()
# GLOBAL_CONFIG.read_file()
DEFAULT_CONFIG = AgentConfig(
    ipv6=False,
    socket_timeout=5,
    recv_timeout=5,
    buf_size=4096,
    server_host='127.0.0.1',
    server_port_node=7000,
    server_port_health=7001,
    # function_storage_path='/data/functions/',
    function_warehouse='/home/vancior/Documents/senior/oss_functions',
    redis_host='127.0.0.1',
    redis_port=6379
)
DEFAULT_CONFIG.update(os.environ)
GLOBAL_CONFIG['DEFAULT'] = DEFAULT_CONFIG
