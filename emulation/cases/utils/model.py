import os


def random_guid(length=4):
    return os.urandom(length).hex()


class Topo:
    def __init__(self):
        pass


class CloudInstance:
    def __init__(self, name=None):
        if name is None:
            name = 'cloud-' + random_guid()


class FogInstance:
    def __init__(self, name=None):
        if name is None:
            name = 'fog-' + random_guid()


class DeviceInstance:
    def __init__(self, name=None):
        if name is None:
            name = 'device-' + random_guid()
