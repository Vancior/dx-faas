import aiohttp
import aioredis
import asyncio
import json
import jwt
import logging
import os
import tornado.web
import tornado.websocket

from utils.log import get_logger
from utils.topo import TopoReader


def abs_open(path):
    return open(os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), path)))


logger = get_logger('Test Service')
SIGNATURE = abs_open('../jwt.signature').read()

WORKFLOW_REDIS_HOST = os.getenv('WORKFLOW_REDIS_HOST', '172.17.42.1')
WORKFLOW_REDIS_PORT = 6380


class CheckMixin:
    def _check(self):
        if self.pool is None or self.json is None:
            self.send_error(500)
            return False
        return True


class BaseHandler(tornado.web.RequestHandler):
    # def initialize(self, db_pool, config):
    #     self.pool = db_pool
    #     self.config = config
    def initialize(self, topo):
        self.topo = topo

    def prepare(self):
        # parse json body
        if self.request.method == 'POST':
            content_type = self.request.headers.get('Content-Type')
            if isinstance(content_type, str) and 'application/json' in content_type.lower():
                self.json = json.loads(self.request.body)
            else:
                self.json = None
        else:
            self.json = None

        # get current user id
        user_token = self.get_cookie('user-token')
        if user_token is not None:
            try:
                payload = jwt.decode(user_token,
                                     SIGNATURE,
                                     algorithms=['HS256'])
                if payload.get('id') is not None:
                    self.current_user = payload['id']
                else:
                    self.current_user
            except jwt.InvalidSignatureError:
                logger.error('jwt error')
                self.current_user = None
        else:
            self.current_user = None


class TestFunctionHandler(BaseHandler):
    @tornado.web.authenticated
    async def post(self):
        # assert self._check()
        """
        {
            'ip': '',
            'uri': '',
            'data': ''
        }
        """

        status = 'success'
        info = ''
        data = {}
        try:
            device = self.topo.ip_to_device(self.json['ip'])
            if device is None:
                raise RuntimeError("device node not exist")
            async with aiohttp.ClientSession() as session:
                async with session.post(f'http://{self.json["ip"]}:6007',
                                        json={
                                            'type': 'function',
                                            'name': self.json['uri'],
                                            'data': self.json['data']}) as resp:
                    data = await resp.json()
                    # text = await resp.text()
                    # data = json.loads(text)
        except Exception as e:
            status = 'fail'
            info = repr(e)
        self.write({'status': status, 'info': info, 'data': data})


async def send_workflow(record_id, ip, uri, data):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(f'http://{ip}:6007',
                                    json={
                                        'type': 'workflow',
                                        'record_id': record_id,
                                        'name': uri,
                                        'data': data
                                    }) as resp:
                data = await resp.json()
    except Exception as e:
        logger.error(e)
        logger.exception('errmsg')


class TestWorkflowHandler(BaseHandler):
    @tornado.web.authenticated
    async def post(self):
        status = 'success'
        info = ''
        data = ''
        try:
            workflow_record_id = os.urandom(16).hex()
            device = self.topo.ip_to_device(self.json['ip'])
            if device is None:
                raise RuntimeError('device node not exist')
            asyncio.get_event_loop().create_task(send_workflow(
                workflow_record_id, self.json['ip'], self.json['uri'], self.json['data']))
            data = workflow_record_id
        except Exception as e:
            status = 'fail'
            info = repr(e)
        self.write({'status': status, 'info': info, 'data': data})


class WSHandler(tornado.websocket.WebSocketHandler):
    async def open(self, record_id):
        logger.info(self.path_args)
        loop = asyncio.get_event_loop()
        self.running = True
        try:
            self.redis_conn = await aioredis.create_redis(
                f'redis://{WORKFLOW_REDIS_HOST}:{WORKFLOW_REDIS_PORT}', loop=loop)
            while self.running:
                data = await self.redis_conn.blpop(f'workflow_record_{self.path_args[0]}', timeout=1)
                if data is None:
                    continue
                else:
                    self.write_message(data[1].decode())
        except Exception as e:
            self.write_message(repr(e))
            self.close()
        # self.redis_client = redis.Redis(
        #     host=WORKFLOW_REDIS_HOST, port=WORKFLOW_REDIS_PORT)
        # pubsub = self.redis_client.pubsub()
        # pubsub.subscribe(f'__keyspace@0__:workflow_record_{self.path_args[0]}')
        # for msg in pubsub.listen():
        #     logger.info(msg)
        #     if isinstance(msg['data'], bytes) and msg['data'].decode() == 'rpush':
        #         data = self.redis_client.lpop(
        #             f'workflow_record_{self.path_args[0]}')
        #         self.write_message(data)
        # print(msg)
        # msg['channel'] = str(msg['channel'], encoding='utf-8')
        # self.write_message(str(msg, encoding='utf-8'))

    def on_message(self, message):
        logger.info(message)

    def on_close(self):
        # self.redis_client.close()
        self.running = False
        logger.info('close')


if __name__ == '__main__':
    topo = TopoReader().read(f'/data/topos/{os.getenv("TOPO_NAME")}.topo')
    handlers = [
        (r'/test/function', TestFunctionHandler, dict(topo=topo)),
        (r'/test/workflow', TestWorkflowHandler, dict(topo=topo)),
        (r'/test/ws/(\w*)', WSHandler)]
    application = tornado.web.Application(handlers=handlers)

    application.listen(8884)
    try:
        tornado.ioloop.IOLoop.current().start()
    except KeyboardInterrupt:
        pass
