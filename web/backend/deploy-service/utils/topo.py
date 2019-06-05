import networkx as nx
from collections import defaultdict


class Object:
    def __str__(self):
        result = []
        for k, v in self.__dir__:
            result.append(f'{k}: {str(v)}')
        return '\t'.join(result)


def dict_to_object(**kwargs):
    obj = Object()
    for k, v in kwargs.items():
        setattr(obj, k, v)
    return obj


# class Switch:
#     def __init__(self, sid, stype):
#         self.sid = sid
#         self.stype = stype
#         self.fogs = []
#         self.devices = []

#     def add_fog(self, fog):
#         self.fogs.append(fog)

#     def add_device(self, device):
#         self.devices.append(device)

# class Device:
#     def __init__(self, did, ip, cpu, memory, switch, delay, bd):
#         self.did = did
#         self.ip = ip
#         self.cpu = cpu
#         self.memory = memory
#         self.switch = switch
#         self.delay = delay
#         self.bd = bd

# class Fog:
#     def __init__(self, fid, ip, cpu, memory, switch, delay, bd):
#         self.fid = fid
#         self.ip = ip
#         self.cpu = cpu
#         self.memory = memory
#         self.memory_occupy = self.memory * 0.2  # reserved
#         self.switch = switch
#         self.delay = delay
#         self.bd = bd

#     def capable(self, cpu_req, memory_req):
#         if self.memory - self.memory_occupy > memory_req:
#             return True
#         return False

#     def occupy(self, cpu_req, memory_req):
#         self.memory_occupy += memory_req

# class Cloud:
#     def __init__(self, cid, ip, cpu, memory, switch, delay, bd):
#         self.cid = cid
#         self.ip = ip
#         self.cpu = cpu
#         self.memory = memory
#         self.switch = switch
#         self.delay = delay
#         self.bd = bd


class Topo:
    def __init__(self, switches, links, devices, fogs, clouds):
        self.switches = switches
        self.links = links
        self.switch_fogs = defaultdict(list)
        self.switch_devices = defaultdict(list)

        self.devices = devices
        self.device_ip_index = {}
        for k, v in devices.items():
            self.device_ip_index[v.ip] = v
            self.switch_devices[v.sid].append(k)

        self.fogs = fogs
        self.fog_ip_index = {}
        for k, v in fogs.items():
            self.fog_ip_index[v.ip] = v
            self.switch_fogs[v.sid].append(k)

        self.clouds = clouds
        self.graph = nx.Graph()
        for l in links:
            self.graph.add_edge(l[0], l[1], delay=l[2], bw=l[3])

    def ip_to_device(self, ip):
        if ip in self.device_ip_index.keys():
            return self.device_ip_index[ip]
        return None
    
    def ip_to_fog(self, ip):
        if ip in self.fog_ip_index.keys():
            return self.fog_ip_index[ip]
        return None

    def switch(self, sid):
        return self.switches[sid]


class TopoReader:
    def __init__(self):
        pass

    def read(self, topo_file):
        topo = None
        with open(topo_file) as topo:
            _, switch_count = topo.readline().split()
            switches = {}
            for i in range(int(switch_count)):
                sid, stype = topo.readline().split()
                sid = int(sid)
                switches[sid] = dict_to_object(sid=sid, stype=stype)
            topo.readline()

            _, switch_link_count = topo.readline().split()
            links = []
            for i in range(int(switch_link_count)):
                s_from, s_to, delay, bd = topo.readline().split()
                links.append((int(s_from), int(s_to), float(delay), float(bd)))
            topo.readline()

            _, cloud_count = topo.readline().split()
            clouds = {}
            for i in range(int(cloud_count)):
                cid, ip, cpu, memory, sid, delay, bd = topo.readline().split()
                cid = int(cid)
                sid = int(sid)
                clouds[cid] = dict_to_object(
                    cid=cid,
                    ip=ip,
                    cpu=int(cpu),
                    memory=int(memory),
                    sid=sid,
                    delay=float(delay),
                    bd=float(bd))
            topo.readline()

            _, fog_count = topo.readline().split()
            fogs = {}
            for i in range(int(fog_count)):
                fid, ip, cpu, memory, sid, delay, bd = topo.readline().split()
                fid = int(fid)
                sid = int(sid)
                fogs[fid] = dict_to_object(
                    fid=fid,
                    ip=ip,
                    cpu=int(cpu),
                    memory=int(memory),
                    sid=sid,
                    delay=float(delay),
                    bd=float(bd))
                # switches[sid].add_fog(fogs[did])
            topo.readline()

            _, device_count = topo.readline().split()
            devices = {}
            for i in range(int(device_count)):
                did, ip, cpu, memory, sid, delay, bd = topo.readline().split()
                did = int(did)
                sid = int(sid)
                devices[did] = dict_to_object(
                    did=did,
                    ip=ip,
                    cpu=int(cpu),
                    memory=int(memory),
                    sid=sid,
                    delay=float(delay),
                    bd=float(bd))

            # TODO 这里其实可以搞到redis里去
            topo = Topo(switches, links, devices, fogs, clouds)
        return topo
