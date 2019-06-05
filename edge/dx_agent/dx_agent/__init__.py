import configparser

GLOBAL_CONFIG = configparser.ConfigParser()
# GLOBAL_CONFIG.read_file()
DEFAULT_CONFIG = dict(
    ipv6=False,
    agent_recv_command_port=10007
)
print(DEFAULT_CONFIG)
GLOBAL_CONFIG['DEFAULT'] = DEFAULT_CONFIG
