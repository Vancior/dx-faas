import asyncio
import json
import logging
import msgpack
import os
import struct

fog_nodes = dict()
logger = logging.getLogger('Cloud')

async def recvmsg(reader, timeout=None):
    """
    Error: asyncio.TimeoutError
    """
    data = None
    head = await asyncio.wait_for(reader.readexactly(4), timeout)
    length = struct.unpack('>I', head)[0]
    data = await reader.readexactly(length)
    data = msgpack.unpackb(data, raw=False)
    return data


def relative_path(path):
    return os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), path))


def packmsg(msg):
    msg_bytes = msgpack.packb(msg, use_bin_type=True)
    meta_bytes = struct.pack('>I', len(msg_bytes))
    return meta_bytes + msg_bytes


async def client_connect_cb(reader, writer):
    host, port = writer.transport.get_extra_info('peername')
    print(host, port)
    fog_nodes[f'{host}:{port}'] = (reader, writer)
    data = await recvmsg(reader)
    writer.write(packmsg({'status': 'success'}))
    # await writer.drain()
    # writer.close()
    print(data)


async def main(host, port):
    server = await asyncio.start_server(client_connect_cb, host=host, port=port)
    print(f'serving on {server.sockets[0].getsockname()}')
    async with server:
        await server.serve_forever()


async def clock():
    cmd_sent = False
    while True:
        print(fog_nodes)
        for key in list(fog_nodes.keys()):
            if fog_nodes[key][1].is_closing():
                logger.info(f'{key} closed')
                fog_nodes.pop(key)
        for key, (reader, writer) in fog_nodes.items():
            if not cmd_sent:
                cmd = json.load(open(relative_path('../function.json')))
                logger.error(repr(cmd))
                writer.write(packmsg(cmd))
                try:
                    resp = await recvmsg(reader, timeout=3)
                    logger.error('***\n{}\n***'json.dumps(resp))
                    cmd_sent = True
                except Exception as e:
                    logger.error(repr(e))
                    cmd_sent = False
            else:
                # NOTE health check
                writer.write(
                    packmsg({'category': 'none', 'action': 'none', 'data': list()}))
            # writer.write(packmsg({'status': 'success'}))
        await asyncio.sleep(5)


async def gather(host, port):
    await asyncio.gather(main(host, port), clock())

if __name__ == '__main__':
    # loop = asyncio.get_event_loop()
    # print(loop)
    # loop = asyncio.new_event_loop()
    # asyncio.set_event_loop(loop)
    # task_main = asyncio.create_task(main('', 7000))
    # task_clock = asyncio.create_task(clock())
    # loop.run_forever()
    asyncio.run(gather('', 7000))
