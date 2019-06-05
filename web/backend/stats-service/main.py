import aioredis
import asyncio
import coloredlogs
import json
import logging
import random
import time
import tornado.ioloop
import tornado.web
import tornado.websocket


logger = logging.getLogger('Stats Service')

coloredlogs.install(
    logger=logger,
    level='DEBUG',
    fmt='%(asctime)s %(name)s[%(process)d] %(levelname)s %(message)s')

REDIS_HOST = os.getenv('WORKFLOW_REDIS_HOST', '172.17.42.1')
REDIS_PORT = 6380


class WorkflowWSHandler(tornado.websocket.WebSocketHandler):
    async def open(self, function_uri):
        self.running = True
        conn = await aioredis.create_connection(f'redis://{REDIS_HOST}:{REDIS_PORT}')
        while self.running:
            timestamp = int(time.time())
            value = await conn.execute('get', 'workflow/' + function_uri)
            if value is None:
                number = 0
            else:
                number = int(value.decode())
            self.write_message(json.dumps(
                {'timestamp': timestamp, 'number': number}))
            await asyncio.sleep(1)

    async def on_message(self, message):
        logger.info(message)

    async def on_close(self):
        self.running = False
        logger.info('close')


class FunctionWSHandler(tornado.websocket.WebSocketHandler):
    async def open(self, function_uri):
        self.running = True
        conn = await aioredis.create_connection(f'redis://{REDIS_HOST}:{REDIS_PORT}')
        while self.running:
            timestamp = int(time.time())
            value = await conn.execute('get', 'function/' + function_uri)
            if value is None:
                number = 0
            else:
                number = int(value.decode())
            self.write_message(json.dumps(
                {'timestamp': timestamp, 'number': number}))
            await asyncio.sleep(5)
            # time.sleep(1)

    async def on_message(self, message):
        logger.info(message)

    async def on_close(self):
        self.running = False
        logger.info('close')


class RequestWSHandler(tornado.websocket.WebSocketHandler):
    async def open(self, uri):
        self.running = True
        conn = await aioredis.create_connection(f'redis://{REDIS_HOST}:{REDIS_PORT}')
        while self.running:
            timestamp = int(time.time())
            value = await conn.execute('getset', 'request/' + uri, 0)
            if value is None:
                number = 0
            else:
                number = int(value.decode())
            self.write_message(json.dumps(
                {'timestamp': timestamp, 'number': number}))
            await asyncio.sleep(5)

    async def on_message(self, message):
        logger.info(message)

    async def on_close(self):
        self.running = False
        logger.info('close')


if __name__ == '__main__':
    handlers = [
        (r'/stats/ws/function/(.*)', FunctionWSHandler),
        (r'/stats/ws/request/(.*)', RequestWSHandler),
    ]
    application = tornado.web.Application(handlers=handlers)
    application.listen(8885)
    try:
        tornado.ioloop.IOLoop.current().start()
    except KeyboardInterrupt:
        pass
