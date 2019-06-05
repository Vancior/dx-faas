import aiomysql
import asyncio
import bcrypt
import coloredlogs
import json
import jwt
import logging
import minio
import os
import subprocess
import tornado.ioloop
import tornado.web

from datetime import timedelta


def abs_open(path):
    return open(os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), path)))


LOGGER = logging.getLogger()
# SIGNATURE = os.urandom(16).hex()
SIGNATURE = abs_open('../jwt.signature').read()
# COOKIE_SECRET = os.urandom(16).hex()
COOKIE_SECRET = abs_open('../cookie.secret').read()
MYSQL_HOST = os.getenv('MYSQL_HOST', '172.17.42.1')
MINIO_HOST = os.getenv('MINIO_HOST', '219.224.171.217:9000')

coloredlogs.install(
    logger=LOGGER,
    level='DEBUG',
    fmt='%(asctime)s %(name)s[%(process)d] %(levelname)s %(message)s')


class CheckMixin:
    def _check(self):
        if self.pool is None or self.json is None:
            self.send_error(500)
            return False
        return True


class BaseHandler(tornado.web.RequestHandler):
    def initialize(self, db_pool, config):
        self.pool = db_pool
        self.config = config

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
                LOGGER.error('jwt error')
                self.current_user = None
        else:
            self.current_user = None


class CreateFunctionHandler(BaseHandler, CheckMixin):
    @tornado.web.authenticated
    async def post(self):
        assert self._check()

        status = 'success'
        info = ''
        try:
            async with self.pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    self.json['uid'] = self.current_user
                    self.json['code_url'] = 'http://{}/user-{}/{}'.format(
                        MINIO_HOST, self.current_user, self.json['uri'])
                    self.json['uri'] = f'user-{self.current_user}/{self.json["uri"]}'
                    await cursor.execute("INSERT INTO `functions` (`uid`, `name`, `uri`, `cpu_limit`, `memory_limit`, `max_idle_time`, `environment`, `handler`, `initializer`, `code_url`, `status`) " +
                                         "VALUES (%(uid)s, %(name)s, %(uri)s, %(cpu_limit)s, %(memory_limit)s, %(max_idle_time)s, %(environment)s, %(handler)s, %(initializer)s, %(code_url)s, 'running')",
                                         self.json)
                    LOGGER.debug(cursor._last_executed)
                    if cursor.rowcount != 1:
                        status = 'fail'
                        info = 'unexpected row count: {}'.format(
                            cursor.rowcount)
                    else:
                        await conn.commit()
        except Exception as e:
            status = 'fail'
            info = repr(e)
        self.write({'status': status, 'info': info})


class ValidateFunctionHandler(CheckMixin, BaseHandler):
    @tornado.web.authenticated
    async def post(self):
        assert self._check()

        # NOTE 验证URI是否重复
        uri = self.json['uri']
        status = 'success'
        info = ''
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    'SELECT * FROM functions WHERE uid=%s AND uri=%s',
                    (self.current_user, uri))
                if cursor.rowcount != 0:
                    status = 'fail'
                    info = 'the URI already exists'
        self.write({'status': status, 'info': info})


class UploadTokenHandler(BaseHandler, CheckMixin):
    def initialize(self, db_pool, config, minio_client):
        super().initialize(db_pool, config)
        self.minio_client = minio_client

    @tornado.web.authenticated
    async def post(self):
        assert self._check()

        # NOTE 调用mc工具生成上传链接的curl命令，并解析curl命令
        uri = self.json['uri']
        status = 'success'
        info = ''
        data = ''
        try:
            data = self.minio_client.presigned_put_object(
                f"user-{self.current_user}", uri, expires=timedelta(minutes=10))
            # data = data.replace(MYSQL_HOST, '192.168.106.164')
        except Exception as e:
            status = 'fail'
            info = repr(e)
        # proc = await asyncio.create_subprocess_exec(
        #     'mc', 'share', 'upload', '-E', '1m',
        #     f"{self.config.get('oss_name')}/user-{self.current_user}/{uri}",
        #     stdout=asyncio.subprocess.PIPE,
        #     stderr=asyncio.subprocess.PIPE)
        # stdout, stderr = await proc.communicate()
        # status = 'success'
        # info = ''
        # data = {}
        # if stderr:
        #     status = 'fail'
        #     info = stderr.decode('utf-8')
        # else:
        #     result = stdout.decode('utf-8')
        #     arg_list = result.split('\n')[2].split(' ')
        #     oss_url = arg_list[2]
        #     form_args = [a.split('=') for a in arg_list[4:-2:2]]
        #     data['url'] = oss_url
        #     data['args'] = form_args
        self.write({'status': status, 'info': info, 'data': data})


class FunctionHandler(BaseHandler):
    @tornado.web.authenticated
    async def get(self):
        if self.pool is None:
            self.send_error(500)
            return
        status = 'success'
        info = ''
        data = []
        try:
            async with self.pool.acquire() as conn:
                async with conn.cursor(aiomysql.cursors.DictCursor) as cursor:
                    await cursor.execute(
                        'SELECT * FROM functions WHERE uid=%s',
                        (self.current_user,))
                    for r in await cursor.fetchall():
                        data.append(r)
        except Exception as e:
            status = 'fail'
            info = repr(e)
        self.write({'status': status, 'info': info, 'data': data})


pool = None
minio_client = None


async def mysql_init(loop):
    global pool, minio_client
    pool = await aiomysql.create_pool(
        host=MYSQL_HOST,
        # host='172.17.42.1',
        port=32768,
        user='root',
        password='924597121',
        db='dx_web',
        loop=loop)
    minio_client = minio.Minio(
        MINIO_HOST,
        # '192.168.106.164:9000',
        # f'{MYSQL_HOST}:9000',
        access_key='Vancior',
        secret_key='924597121',
        secure=False)


async def mysql_exit():
    pool.close()
    await pool.wait_closed()


if __name__ == '__main__':
    config = {'oss_name': 'minio'}
    # initialize mysql
    tornado.ioloop.IOLoop.current().run_sync(lambda: mysql_init(
        asyncio.get_event_loop()))
    # create tornado application
    settings = {'cookie_secret': COOKIE_SECRET, 'login_url': '/login'}
    handlers = [
        (r"/function/create", CreateFunctionHandler,
         dict(db_pool=pool, config=config)),
        (r"/function/validate", ValidateFunctionHandler,
         dict(db_pool=pool, config=config)),
        (r"/function/token", UploadTokenHandler,
         dict(db_pool=pool, config=config, minio_client=minio_client)),
        (r"/function", FunctionHandler, dict(db_pool=pool, config=config))
    ]
    application = tornado.web.Application(handlers=handlers, **settings)

    application.listen(8881)
    # tornado.ioloop.IOLoop().spawn_callback(mysql_init, loop=tornado.ioloop.IOLoop().current())
    try:
        tornado.ioloop.IOLoop.current().start()
    except KeyboardInterrupt:
        # close mysql
        tornado.ioloop.IOLoop.current().run_sync(mysql_exit)
