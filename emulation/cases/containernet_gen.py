import sys
import random

FILE_HEAD = """
import docker
import mininet.cli
import mininet.node
import mininet.link
import mininet.log
import mininet.net
import os
import sys
import time
from functools import partial

mininet.log.setLogLevel('info')

Switch = partial(mininet.node.OVSSwitch, protocols='OpenFlow13')
net = mininet.net.Containernet(switch=Switch)
net.addController('c0', controller=mininet.node.RemoteController, ip='172.17.42.1', port=6652)

# runtime_id = os.urandom(2).encode('hex')
runtime_id = sys.argv[1]
"""
FILE_TAIL_1 = """
net.start()
net.ping([{}])
"""
FILE_TAIL_2 = """
client = docker.from_env().api
while True:
    device_count = 0
    for c in client.containers():
        if 'dx_device' in c['Image']:
            device_count += 1
    if device_count == 0:
        break
    else:
        time.sleep(60)
# mininet.cli.CLI(net)
net.stop()
"""
CPU_PERIOD = 100000


def parse_args():
    # topo file prefix
    return sys.argv[1]


def parse_file(topo_name, topo_filename, output_filename):
    with open(topo_filename) as topo, open(output_filename, 'w') as output:
        output.write(FILE_HEAD)
        _, switch_count = topo.readline().split()
        switch_template = """{} = net.addSwitch("{}")\n"""
        for i in range(int(switch_count)):
            sid, stype = topo.readline().split()
            sid = 's' + sid
            output.write(switch_template.format(sid, sid))
        topo.readline()

        ping_list = []
        link_template = """net.addLink({}, {}, cls=mininet.link.TCLink, delay="{}ms", bw={})\n"""

        _, switch_link_count = topo.readline().split()
        for i in range(int(switch_link_count)):
            s_from, s_to, delay, bw = topo.readline().split()
            output.write(
                link_template.format('s' + s_from, 's' + s_to, delay, bw))
        topo.readline()

        cloud_list = []
        _, cloud_count = topo.readline().split()
        cloud_template = """
{} = net.addDocker(
    '{}' + runtime_id,
    ip='{}/8',
    dimage='dx_cloud',
    # dcmd='python deploy-service/main.py',
    dcmd='./boot.sh',
    # dcmd='tail -f /dev/null',
    environment={{
        'TOPO_NAME': '{}',
        'CADVISOR_HOST': '172.17.42.1',
        'CADVISOR_PORT': 9001
    }},
    volumes=['/home/hujuntao/gitrepo/dx-proto/emulation/cases:/data/topos'],
    cpu_quota={},
    mem_limit='{}m')
"""
        for i in range(int(cloud_count)):
            cid, ip, cpu, memory, sid, delay, bw = topo.readline().split()
            cid = 'c' + cid
            sid = 's' + sid
            output.write(
                cloud_template.format(cid, cid, ip, topo_name,
                                      int(cpu) * CPU_PERIOD, memory))
            output.write(link_template.format(cid, sid, delay, bw))
            ping_list.append(cid)
            cloud_list.append(cid)
        topo.readline()

        fog_list = []
        _, fog_count = topo.readline().split()
        fog_template = """
{} = net.addDocker(
    '{}' + runtime_id,
    ip='{}/8',
    dimage='dx_edge',
    dcmd='bash boot.sh',
    # dcmd='tail -f /dev/null',
    environment={{
        'MY_IP': '{}',
        'SERVER_HOST': '10.0.1.1',
        'SERVER_PORT_NODE': 7000,
        'START_DELAY': 20,
        'AGENT_MODE': 'dev',
        'FUNCTION_WAREHOUSE': '/home/hujuntao/deploy/functions'
    }},
    volumes=[
        '/var/run/docker.sock:/var/run/docker.sock',
        '/home/hujuntao/deploy/functions:/home/hujuntao/deploy/functions',
    ],
    cpu_quota={},
    mem_limit='{}m')
"""
        for i in range(int(fog_count)):
            fid, ip, cpu, memory, sid, delay, bw = topo.readline().split()
            fid = 'f' + fid
            sid = 's' + sid
            output.write(
                fog_template.format(fid, fid, ip, ip,
                                    int(cpu) * CPU_PERIOD, memory))
            output.write(link_template.format(fid, sid, delay, bw))
            ping_list.append(fid)
            fog_list.append(fid)
        topo.readline()

        device_list = []
        _, device_count = topo.readline().split()
        device_template = """
{} = net.addDocker(
    '{}' + runtime_id,
    ip='{}/8',
    dimage='dx_device:latest',
    dcmd='python -m dx_emulation.scalar',
    # dcmd='tail -f /dev/null',
    environment={{
        'MY_IP': '{}',
        'CLOUD_HOST': '10.0.1.1',
        'CLOUD_PORT': 8883,
        'START_TIME': {},
        'RUN_INTERVAL': 1,
        'RUN_COUNT': 50,
        'EMULATION_MODE': 'dev',
        'LOG_FILE': '/data/log/{}' + runtime_id + '.log'
    }},
    volumes=['/home/hujuntao/log/device:/data/log'],
    cpu_quota={},
    mem_limit='{}m')
"""
        for i in range(int(device_count)):
            did, ip, cpu, memory, sid, delay, bw = topo.readline().split()
            did = 'd' + did
            sid = 's' + sid
            output.write(
                device_template.format(did, did, ip, ip, 30 + random.randint(0, 50), did, int(cpu) * CPU_PERIOD, memory))
            output.write(link_template.format(did, sid, delay, bw))
            ping_list.append(did)
            device_list.append(did)

        output.write(FILE_TAIL_1.format(', '.join(ping_list)))
        # for i in cloud_list:
        #     output.write(f'{i}.sendCmd("python deploy-service/main.py &")\n')
        # for i in fog_list:
        #     output.write(f'{i}.sendCmd("bash boot.sh &")\n')
        # for i in device_list:
        #     output.write(f'{i}.sendCmd("python -m dx_emulation.scalar &")\n')
        output.write(FILE_TAIL_2)


def main():
    topo_name = parse_args()
    parse_file(topo_name, topo_name + '.topo', topo_name + '.py')


if __name__ == '__main__':
    main()
