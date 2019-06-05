import configparser

GLOBAL_CONFIG = configparser.ConfigParser()
# GLOBAL_CONFIG.read_file()
DEFAULT_CONFIG = dict(
    ipv6=False,
    socket_timeout=5,
    recv_timeout=5,
    buf_size=4096,
    server_address='101.132.189.168',
    agent_recv_command_port=10007,
    # function_storage_path='/data/functions/'
    function_storage_path='/home/vancior/Documents/senior/oss_functions',
    redis_port=6379
)
GLOBAL_CONFIG['DEFAULT'] = DEFAULT_CONFIG
