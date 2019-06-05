import aiomysql
import asyncio
import bcrypt
import coloredlogs
import json
import jwt
import logging
import minio
import os
import time
import tornado.ioloop
import tornado.web

from datetime import datetime, timedelta


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


class BaseHandler(tornado.web.RequestHandler):

    # def set_default_headers(self):
    #     self.set_header("Access-Control-Allow-Origin", "http://localhost:8080")
    #     self.set_header("Access-Control-Allow-Credentials", "true")
    #     self.set_header("Access-Control-Allow-Headers", "Content-Type")
    #     self.set_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')

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

        # get current user id
        # user_token = self.get_secure_cookie('user-token')
        user_token = self.get_cookie('user-token')
        if user_token is not None:
            try:
                payload = jwt.decode(user_token,
                                     SIGNATURE,
                                     algorithms=['HS256'])
                # LOGGER.debug(json.dumps(payload))
                if payload.get('id') is not None:
                    self.current_user = payload['id']
                else:
                    self.current_user = None
            except jwt.InvalidSignatureError:
                LOGGER.error('jwt error')
                self.current_user = None
        else:
            self.current_user = None

    def options(self):
        self.set_status(204)
        self.finish()


class EmailValidateHandler(BaseHandler):
    async def post(self):
        # if self.current_user is not None:
        #     self.redirect('/center')
        #     return
        if self.pool is None or self.json is None:
            self.send_error(500)
            return
        status = 'success'
        info = ''
        try:
            async with self.pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(
                        "SELECT * FROM users WHERE email=%(email)s",
                        self.json)
                    if cursor.rowcount != 0:
                        status = 'fail'
                        info = 'email already taken'
        except Exception as e:
            status = 'fail'
            info = repr(e)
        self.write({'status': status, 'info': info})


class RegisterHandler(BaseHandler):
    def initialize(self, db_pool, config, minio_client):
        super().initialize(db_pool, config)
        self.minio_client = minio_client

    async def post(self):
        # if self.current_user is not None:
        #     self.redirect('/center')
        #     return
        if self.pool is None or self.json is None:
            self.send_error(500)
            return
        status = 'success'
        info = ''
        try:
            async with self.pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(
                        "SELECT * FROM `users` WHERE email=%(email)s",
                        self.json)
                    if cursor.rowcount == 0:
                        self.json['password'] = bcrypt.hashpw(
                            bytes(self.json['password'], 'ascii'), bcrypt.gensalt()).decode('ascii')
                        self.json['ak'] = os.urandom(32).hex()
                        self.json['sk'] = os.urandom(32).hex()
                        await cursor.execute("INSERT INTO `users` (`email`, `nickname`, `ak`, `sk`, `password`)" +
                                             " VALUES (%(email)s, %(email)s, %(ak)s, %(sk)s, %(password)s)",
                                             self.json)
                        if cursor.rowcount != 1:
                            status = 'fail'
                            info = 'unexpected row count: {}'.format(
                                cursor.rowcount)
                        else:
                            # NOTE 在OSS创建用户对应的bucket
                            try:
                                self.minio_client.make_bucket(
                                    f'user-{cursor.lastrowid}')
                                await conn.commit()
                            except Exception as e:
                                status = 'fail'
                                info = repr(e)
                            # proc = await asyncio.create_subprocess_exec(
                            #     '/download/mc',
                            #     'mb',
                            #     f"{self.config.get('oss_name')}/user-{cursor.lastrowid}",
                            #     stdout=asyncio.subprocess.PIPE,
                            #     stderr=asyncio.subprocess.PIPE)
                            # stdout, stderr = await proc.communicate()
                            # if stderr:
                            #     status = 'fail'
                            #     info = stderr.decode('utf-8')
                            # else:
                            #     info = stdout.decode('utf-8')
                            #     await conn.commit()
                    else:
                        status = 'fail'
                        info = 'email already taken'
        except Exception as e:
            status = 'fail'
            info = repr(e)
        self.write({'status': status, 'info': info})


class LogInHandler(BaseHandler):
    async def post(self):
        # if self.current_user is not None:
        #     self.redirect('/center')
        #     return
        if self.pool is None or self.json is None:
            self.send_error(500)
            return
        status = 'success'
        info = ''
        try:
            async with self.pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(
                        "SELECT id, password FROM users WHERE email=%(email)s",
                        self.json)
                    result = await cursor.fetchone()
                    print(result)
                    if result is None:
                        status = 'fail'
                        info = '账户不存在'
                    else:
                        uid, pwd = result
                        if bcrypt.checkpw(bytes(self.json['password'], 'ascii'),
                                          bytes(pwd, encoding='ascii')):
                            user_token = jwt.encode({'id': uid},
                                                    SIGNATURE,
                                                    algorithm='HS256')
                            # self.set_secure_cookie('user-token', user_token)
                            self.set_cookie(
                                'user-token', user_token, expires=(datetime.now() + timedelta(weeks=1)).timestamp())
                        else:
                            status = 'fail'
                            info = '密码错误'
        except Exception as e:
            status = 'fail'
            info = repr(e)
        self.write({'status': status, 'info': info})


class VerifyHandler(BaseHandler):
    async def get(self):
        status = 'success'
        info = ''
        if self.current_user is None:
            status = 'fail'
        self.write({'status': status, 'info': info})


class UserInfoHandler(BaseHandler):
    @tornado.web.authenticated
    async def get(self):
        status = 'success'
        info = ''
        data = {}
        try:
            async with self.pool.acquire() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cursor:
                    await cursor.execute(
                        "SELECT email, nickname, ak, sk FROM users WHERE id=%s",
                        self.current_user)
                    if cursor.rowcount != 1:
                        status = 'fail'
                        info = 'user not found'
                    else:
                        data = await cursor.fetchone()
        except Exception as e:
            LOGGER.error(e)
            LOGGER.exception('errmsg')
            status = 'fail'
            info = repr(e)
        self.write({'status': status, 'info': info, 'data': data})

# NOTE no need for a LogOutHandler, just delete cookie in the browser


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
    handlers = [(r"/user/register", RegisterHandler,
                 dict(db_pool=pool, config=config, minio_client=minio_client)),
                (r"/user/login", LogInHandler,
                 dict(db_pool=pool, config=config)),
                (r"/user/validate", EmailValidateHandler,
                 dict(db_pool=pool, config=config)),
                (r"/user/verify", VerifyHandler,
                 dict(db_pool=pool, config=config)),
                (r"/user/info", UserInfoHandler,
                 dict(db_pool=pool, config=config))]
    application = tornado.web.Application(handlers=handlers,
                                          cookie_secret=COOKIE_SECRET)
    application.listen(8880)
    # tornado.ioloop.IOLoop().spawn_callback(mysql_init, loop=tornado.ioloop.IOLoop().current())
    try:
        tornado.ioloop.IOLoop.current().start()
    except KeyboardInterrupt:
        # close mysql
        tornado.ioloop.IOLoop.current().run_sync(mysql_exit)
