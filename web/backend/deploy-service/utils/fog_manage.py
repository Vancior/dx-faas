import aiohttp
import aioredis
import asyncio
import coloredlogs
import json
import logging
import msgpack
import os
import struct

from collections import defaultdict
from .log import get_logger

CADVISOR_HOST = os.getenv('CADVISOR_HOST')
CADVISOR_PORT = int(os.getenv('CADVISOR_PORT'))
REDIS_HOST = os.getenv('WORKFLOW_REDIS_HOST', '172.17.42.1')
REDIS_PORT = 6380
# fog_nodes = dict()
# logger = logging.getLogger('Fog Manage')
logger = get_logger('Fog Manage')
# coloredlogs.install(
#     logger=logger,
#     level='DEBUG',
#     fmt='%(asctime)s %(name)s:%(lineno)d[%(process)d] %(levelname)s %(message)s')


def relative_path(path):
    return os.path.abspath(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), path))


async def recvmsg(reader, timeout=None):
    """
    Error: asyncio.TimeoutError
    """
    # head = await asyncio.wait_for(reader.readexactly(4), timeout)
    head = await asyncio.wait_for(reader.read(4), timeout)
    length = struct.unpack('>I', head)[0]
    data = await reader.read(length)
    data = msgpack.unpackb(data, raw=False)
    return data


def packmsg(msg):
    msg_bytes = msgpack.packb(msg, use_bin_type=True)
    meta_bytes = struct.pack('>I', len(msg_bytes))
    return meta_bytes + msg_bytes


class FogNode:
    def __init__(self, ip, cpu_info, memory_info, disk_info, gateway, reader, writer):
        """
        gateway is the openresty port, for avoiding socat overhead
        """
        self.ip = ip
        self.cpu_info = cpu_info
        freq = max(cpu_info['freq']['max'], cpu_info['freq']['min'],
                   cpu_info['freq']['current'])
        self.cpu_quota = cpu_info['count'] * int(
            freq) // 1000  # 4core * 2500MHz // 100
        self.cpu_occupy = 0
        self.memory_info = memory_info
        # self.memory_quota = memory_info['available'] + memory_info['used']
        self.memory_quota = memory_info['total']
        self.memory_occupy = memory_info[
            'used'] * 2  # reserved memory for system running
        self.memory_real = -1
        self.gateway = gateway
        self.reader = reader
        self.writer = writer
        self.lock = asyncio.Lock()
        # function_uri -> runtime_id -> container_id
        self.running_containers = dict()

    def occupy(self, cpu_req, memory_req):
        self.cpu_occupy += cpu_req
        self.memory_occupy += memory_req

    def __str__(self):
        str_list = []
        for k in self.__dir__():
            if k.startswith('cpu') or k.startswith('memory'):
                str_list.append(f'{k}: {getattr(self, k)}')
        return '\t'.join(str_list)


class FogData:
    def __init__(self):
        self.fog_nodes = dict()

    def add_fog(self, ip, cpu_info, memory_info, disk_info, gateway, reader, writer):
        """
        Error: RuntimeError
        """
        if ip in self.fog_nodes.keys():
            raise RuntimeError('ip conflict')
        else:
            self.fog_nodes[ip] = FogNode(ip, cpu_info, memory_info, disk_info, gateway,
                                         reader, writer)

    def __getitem__(self, ip):
        return self.fog_nodes.get(ip)

    def status_all(self):
        return '\n'.join([str(i) for i in self.fog_nodes.values()])


class ContainerData:
    def __init__(self):
        self.containers = dict()
        self.data_lock = asyncio.Lock()
        self.redis_conn = None

    async def _update(self, session, container_id):
        url = f'http://{CADVISOR_HOST}:{CADVISOR_PORT}/api/v2.0/stats/docker/{container_id}?count=1'
        async with session.get(url) as response:
            try:
                data = await response.text()
                if response.status != 200 and data.startswith('unknown container'):
                    uri = self.containers[container_id]['uri']
                    await self.data_lock.acquire()
                    del self.containers[container_id]
                    self.data_lock.release()
                    if uri.startswith('function/'):
                        if self.redis_conn is None:
                            self.redis_conn = await aioredis.create_connection(f'redis://{REDIS_HOST}:{REDIS_PORT}')
                        await self.redis_conn.execute('decr', uri)
                else:
                    data = json.loads(data)
                    key = list(data.keys())[0]
                    self.containers[container_id]['usage'] = data[key][0]['memory']['usage']
            except Exception as e:
                logger.error(e)
                logger.error(data)
                logger.exception('errmsg')

    async def update_status(self):
        keys = list()
        await self.data_lock.acquire()
        try:
            keys = list(self.containers.keys())
        finally:
            self.data_lock.release()
        if len(keys) > 0:
            async with aiohttp.ClientSession() as session:
                wait_list = []
                for i in keys:
                    wait_list.append(self._update(session, i))
                await asyncio.gather(*wait_list)
                # logger.info(f'update {len(keys)} containers')
        # info['spec']['memory']['limit']
        # info['stats']['memory']
        """
        "memory": {
            "usage": 29319168,
            "max_usage": 30064640,
            "cache": 626688,
            "rss": 26783744,
            "swap": 0,
            "mapped_file": 0,
            "working_set": 28692480,
            "failcnt": 0,
            "container_data": {
                "pgfault": 240197,
                "pgmajfault": 0
            },
            "hierarchical_data": {
                "pgfault": 240197,
                "pgmajfault": 0
            }
        },
        """

    async def add_container(self, container_id, memory_limit, function_uri):
        await self.data_lock.acquire()
        try:
            self.containers[container_id] = {
                'limit': memory_limit, 'usage': memory_limit, 'uri': function_uri}
        finally:
            self.data_lock.release()

    def get(self, key):
        return self.containers.get(key)

    def __getitem__(self, key):
        return self.get(key)


class FogManage:
    def __init__(self, host, port, fog_data, container_data):
        self.host = host
        self.port = port
        self.fog_data = fog_data
        self.container_data = container_data

    async def client_connect_cb(self, reader, writer):
        # host, port = writer.transport.get_extra_info('peername')
        # logger.info(f'connection from {host}:{port}')
        status = 'success'
        info = ''
        try:
            data = await recvmsg(reader, timeout=3)
            self.fog_data.add_fog(data['ip'], data['cpu'], data['memory'], data['gateway'], {},
                                  reader, writer)
            logger.info(f'connection from {data["ip"]}')
        except Exception as e:
            status = 'fail'
            info = repr(e)
        writer.write(packmsg({'status': status, 'info': info}))

    async def serve(self):
        server = await asyncio.start_server(
            self.client_connect_cb, host=self.host, port=self.port)
        logger.info(f'fog_manage running on {server.sockets[0].getsockname()}')
        async with server:
            await server.serve_forever()

    async def monitor(self):
        while True:
            await self.container_data.update_status()
            # logger.info('monitoring...')
            await asyncio.sleep(1)

    async def run(self):
        logger.info('running...')
        await asyncio.gather(self.serve(), self.monitor())

    async def send_cmd(self, ip, cmd, timeout=3):
        entry = self.fog_data[ip]
        entry.writer.write(packmsg(cmd))
        await entry.lock.acquire()
        try:
            return await recvmsg(entry.reader, timeout=timeout)
        finally:
            entry.lock.release()

    async def update_container(self, ip, function_uri, runtime_id, containers, memory_limit):
        # logger.info(f'{runtime_id} updated')
        entry = self.fog_data[ip]
        if entry.running_containers.get(function_uri) is None:
            entry.running_containers[function_uri] = dict()
        try:
            await self.container_data.add_container(containers[runtime_id], memory_limit, function_uri)
            entry.running_containers[function_uri][runtime_id] = containers[runtime_id]
        except KeyError:
            logger.critical(containers)
            logger.critical(runtime_id)
