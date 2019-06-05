import coloredlogs
import logging
import networkx as nx
import os

from abc import abstractmethod

from utils.topo import TopoReader
from utils.log import get_logger

# logger = logging.getLogger('Scheduling Algorithm')
logger = get_logger('Scheduling Algorithm')
# coloredlogs.install(
#     logger=logger,
#     level='DEBUG',
#     fmt='%(asctime)s %(name)s:%(lineno)d[%(process)d] %(levelname)s %(message)s')


class Algo:
    @abstractmethod
    def schedule(self):
        pass

    @abstractmethod
    def show_status(self):
        pass


class FirstFitAlgo(Algo):
    def __init__(self, topo_file, fog_data, container_data):
        self.topo = TopoReader().read(topo_file)
        self.fog_data = fog_data
        self.container_data = container_data

    def schedule(self, runtime_id, ip, function_uri, cpu_req, memory_req):
        device = self.topo.ip_to_device(ip)
        if device is None:
            fog = self.topo.ip_to_fog(ip)
            if fog is None:
                logger.critical(ip)
                raise RuntimeError('device not exist in topo')
            else:
                device = fog
        fog_ip = None
        queue = [device.sid]
        found = False
        visited = {}
        while len(queue) > 0:
            # logger.info(repr(queue))
            sid = queue.pop(0)
            visited[sid] = True
            for fid in self.topo.switch_fogs[sid]:
                fog_node = self.fog_data[self.topo.fogs[fid].ip]
                # logger.info(f'device on: {device.sid}, test on: {sid}')
                if fog_node is not None:
                    runtimes = fog_node.running_containers.get(function_uri)
                    # NOTE 测试是否可以复用现有的runtime，标准为内存用量少于限制的1/3
                    if runtimes is not None:
                        for rid, cid in runtimes.items():
                            entry = self.container_data.get(cid)
                            if entry is not None:
                                logger.info(f'{rid}: {entry["limit"]} {entry["usage"]}')
                                if entry['limit'] > 3 * entry['usage']:
                                    found = True
                                    runtime_id = rid
                                    fog_ip = fog_node.ip
                                    # fog_ip = fog_node.gateway
                                    break
                    # logger.info('{} {} {} {} {} {}'.format(fog_node.cpu_quota, fog_node.cpu_occupy, fog_node.memory_quota, fog_node.memory_occupy, cpu_req, memory_req))
                    if not found and fog_node.cpu_quota >= fog_node.cpu_occupy + cpu_req and \
                        fog_node.memory_quota > max(fog_node.memory_occupy, fog_node.memory_real) + memory_req:
                        found = True
                        fog_ip = fog_node.ip
                        # fog_ip = fog_node.gateway
                        fog_node.occupy(cpu_req, memory_req)
                    if found:
                        break
            if found:
                break
            for s in nx.neighbors(self.topo.graph, sid):
                if visited.get(s) is None:
                    queue.append(s)
        if not found:
            raise RuntimeError('insufficient fog nodes')
        return fog_ip, runtime_id

class FirstFitNoReuseAlgo(Algo):
    def __init__(self, topo_file, fog_data, container_data):
        self.topo = TopoReader().read(topo_file)
        self.fog_data = fog_data
        self.container_data = container_data

    def schedule(self, runtime_id, ip, function_uri, cpu_req, memory_req):
        device = self.topo.ip_to_device(ip)
        if device is None:
            fog = self.topo.ip_to_fog(ip)
            if fog is None:
                logger.critical(ip)
                raise RuntimeError('device not exist in topo')
            else:
                device = fog
        fog_ip = None
        queue = [device.sid]
        found = False
        visited = {}
        while len(queue) > 0:
            sid = queue.pop(0)
            visited[sid] = True
            for fid in self.topo.switch_fogs[sid]:
                fog_node = self.fog_data[self.topo.fogs[fid].ip]
                if fog_node is not None:
                    if fog_node.cpu_quota >= fog_node.cpu_occupy + cpu_req and \
                        fog_node.memory_quota > max(fog_node.memory_occupy, fog_node.memory_real) + memory_req:
                        found = True
                        fog_ip = fog_node.ip
                        # fog_ip = fog_node.gateway
                        fog_node.occupy(cpu_req, memory_req)
                    if found:
                        break
            if found:
                break
            for s in nx.neighbors(self.topo.graph, sid):
                if visited.get(s) is None:
                    queue.append(s)
        if not found:
            raise RuntimeError('insufficient fog nodes')
        return fog_ip, runtime_id

    def show_status(self):
        return self.fog_data.status_all()
