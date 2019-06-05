
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
s0 = net.addSwitch("s0")
s1 = net.addSwitch("s1")
s2 = net.addSwitch("s2")
s3 = net.addSwitch("s3")
s4 = net.addSwitch("s4")
net.addLink(s0, s1, cls=mininet.link.TCLink, delay="100ms", bw=40)
net.addLink(s1, s2, cls=mininet.link.TCLink, delay="10ms", bw=20)
net.addLink(s0, s3, cls=mininet.link.TCLink, delay="100ms", bw=40)
net.addLink(s3, s4, cls=mininet.link.TCLink, delay="10ms", bw=20)

c0 = net.addDocker(
    'c0' + runtime_id,
    ip='10.0.1.1/8',
    dimage='dx_cloud',
    # dcmd='python deploy-service/main.py',
    dcmd='./boot.sh',
    # dcmd='tail -f /dev/null',
    environment={
        'TOPO_NAME': 'c1f2d2_edge',
        'CADVISOR_HOST': '172.17.42.1',
        'CADVISOR_PORT': 9001
    },
    volumes=['/home/hujuntao/gitrepo/dx-proto/emulation/cases:/data/topos'],
    cpu_quota=400000,
    mem_limit='4096m')
net.addLink(c0, s0, cls=mininet.link.TCLink, delay="1ms", bw=40)

f0 = net.addDocker(
    'f0' + runtime_id,
    ip='10.0.2.1/8',
    dimage='dx_edge',
    dcmd='bash boot.sh',
    # dcmd='tail -f /dev/null',
    environment={
        'MY_IP': '10.0.2.1',
        'SERVER_HOST': '10.0.1.1',
        'SERVER_PORT_NODE': 7000,
        'START_DELAY': 20,
        'AGENT_MODE': 'dev',
        'FUNCTION_WAREHOUSE': '/home/hujuntao/deploy/functions'
    },
    volumes=[
        '/var/run/docker.sock:/var/run/docker.sock',
        '/home/hujuntao/deploy/functions:/home/hujuntao/deploy/functions',
    ],
    cpu_quota=200000,
    mem_limit='2048m')
net.addLink(f0, s1, cls=mininet.link.TCLink, delay="1ms", bw=20)

f1 = net.addDocker(
    'f1' + runtime_id,
    ip='10.0.2.2/8',
    dimage='dx_edge',
    dcmd='bash boot.sh',
    # dcmd='tail -f /dev/null',
    environment={
        'MY_IP': '10.0.2.2',
        'SERVER_HOST': '10.0.1.1',
        'SERVER_PORT_NODE': 7000,
        'START_DELAY': 20,
        'AGENT_MODE': 'dev',
        'FUNCTION_WAREHOUSE': '/home/hujuntao/deploy/functions'
    },
    volumes=[
        '/var/run/docker.sock:/var/run/docker.sock',
        '/home/hujuntao/deploy/functions:/home/hujuntao/deploy/functions',
    ],
    cpu_quota=200000,
    mem_limit='2048m')
net.addLink(f1, s3, cls=mininet.link.TCLink, delay="1ms", bw=20)

d0 = net.addDocker(
    'd0' + runtime_id,
    ip='10.0.3.1/8',
    dimage='dx_device:latest',
    dcmd='python -m dx_emulation.scalar',
    # dcmd='tail -f /dev/null',
    environment={
        'MY_IP': '10.0.3.1',
        'CLOUD_HOST': '10.0.1.1',
        'CLOUD_PORT': 8883,
        'START_TIME': 61,
        'RUN_INTERVAL': 1,
        'RUN_COUNT': 50,
        'EMULATION_MODE': 'dev',
        'LOG_FILE': '/data/log/d0' + runtime_id + '.log'
    },
    volumes=['/home/hujuntao/log/device:/data/log'],
    cpu_quota=100000,
    mem_limit='128m')
net.addLink(d0, s2, cls=mininet.link.TCLink, delay="1ms", bw=10)

d1 = net.addDocker(
    'd1' + runtime_id,
    ip='10.0.3.2/8',
    dimage='dx_device:latest',
    dcmd='python -m dx_emulation.scalar',
    # dcmd='tail -f /dev/null',
    environment={
        'MY_IP': '10.0.3.2',
        'CLOUD_HOST': '10.0.1.1',
        'CLOUD_PORT': 8883,
        'START_TIME': 34,
        'RUN_INTERVAL': 1,
        'RUN_COUNT': 50,
        'EMULATION_MODE': 'dev',
        'LOG_FILE': '/data/log/d1' + runtime_id + '.log'
    },
    volumes=['/home/hujuntao/log/device:/data/log'],
    cpu_quota=100000,
    mem_limit='128m')
net.addLink(d1, s4, cls=mininet.link.TCLink, delay="1ms", bw=10)

net.start()
net.ping([c0, f0, f1, d0, d1])

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
