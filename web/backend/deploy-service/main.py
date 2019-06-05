import aiomysql
import aioredis
import asyncio
import bcrypt
import coloredlogs
import json
import jwt
import logging
import minio
import os
import random
import subprocess
import time
import tornado.ioloop
import tornado.web
import traceback

from datetime import timedelta

from utils.fog_manage import FogData, ContainerData, FogManage
from utils.log import get_logger
from utils.workflow import WorkflowHelper
from algo import FirstFitAlgo, FirstFitNoReuseAlgo

MYSQL_HOST = os.getenv('MYSQL_HOST', '172.17.42.1')
MINIO_HOST = os.getenv('MINIO_HOST', '219.224.171.217:9000')
REDIS_HOST = os.getenv('WORKFLOW_REDIS_HOST', '172.17.42.1')
REDIS_PORT = 6380


def abs_open(path):
    return open(
        os.path.abspath(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), path)))


def abs_path(path):
    return os.path.abspath(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), path))


# logger = logging.getLogger('Deploy Service')
logger = get_logger('Deploy Service')
# SIGNATURE = os.urandom(16).hex()
SIGNATURE = abs_open('../jwt.signature').read()
# COOKIE_SECRET = os.urandom(16).hex()
COOKIE_SECRET = abs_open('../cookie.secret').read()

# coloredlogs.install(
#     logger=logger,
#     level='DEBUG',
#     fmt='%(asctime)s %(name)s:%(lineno)d[%(process)d] %(levelname)s %(message)s')


class CheckMixin:
    def _check(self):
        if self.pool is None or self.json is None:
            self.send_error(500)
            return False
        return True


class BaseHandler(tornado.web.RequestHandler):
    def initialize(self, redis_pool, db_pool, config, algo, fog_manage):
        self.redis_pool = redis_pool
        self.pool = db_pool
        self.config = config
        self.algo = algo
        self.fog_manage = fog_manage

    def prepare(self):
        # parse json body
        if self.request.method == 'POST':
            content_type = self.request.headers.get('Content-Type')
            if isinstance(content_type,
                          str) and 'application/json' in content_type.lower():
                self.json = json.loads(self.request.body)
            else:
                self.json = None
        else:
            self.json = None


image_table = {
    'python3': 'dx/python3:latest'
}
function_info_cache = dict()


async def pull_function(url, dest):
    try:
        ip, bucket, code = url[7:].split('/')
        data = minio_client.get_object(bucket, code)
        with open(f'{dest}/tmp.zip', 'wb') as zip_file:
            for d in data.stream(32 * 1024):
                zip_file.write(d)
        # wget_proc = await asyncio.create_subprocess_shell(f'wget -O {dest}/tmp.zip {url}')
        # await wget_proc.communicate()
        unzip_proc = await asyncio.create_subprocess_shell(f'unzip -o -d {dest} {dest}/tmp.zip')
        await unzip_proc.communicate()
    except Exception as e:
        logger.error(e)
        logger.exception('errmsg')


class FunctionHandler(BaseHandler, CheckMixin):
    async def post(self):
        # assert self._check()

        status = 'success'
        info = ''
        data = {}
        runtime_id = os.urandom(16).hex()
        # cpu_req = 8
        # memory_req = 512 * 1024 * 1024  # MB to B
        try:
            # function_uri = 'user-1/' + self.json['function']
            function_uri = self.json['function']
            function_info = None
            if function_info_cache.get(function_uri) is None:
                async with self.pool.acquire() as conn:
                    async with conn.cursor(aiomysql.cursors.DictCursor) as cursor:
                        await cursor.execute(f"SELECT * FROM `functions` WHERE uri=%s", function_uri)
                        if cursor.rowcount == 0:
                            raise RuntimeError('function not found')
                        else:
                            function_info = await cursor.fetchone()
                            function_info['memory_limit'] = function_info['memory_limit'] * 1024 * 1024
                            function_info_cache[function_uri] = function_info
            else:
                function_info = function_info_cache[function_uri]
            fog_ip, result_id = self.algo.schedule(
                runtime_id, self.json['ip'], 'function/' + function_uri, function_info['cpu_limit'], function_info['memory_limit'])
            if result_id == runtime_id:
                cmd = {
                    "category": "function",
                    "action": "pullup",
                    "data": [{
                        "uri": function_uri,
                        "runtime_id": runtime_id,
                        "name": function_uri,
                        "image": image_table[function_info['environment']],
                        "source": function_info['code_url'],
                        # f"http://vancior-picgo.oss-cn-beijing.aliyuncs.com/functions/{self.json['function']}/function.zip",
                        "version": "v1.0.0",
                        "workflow": None,
                        "entrypoint": function_info['handler'],
                        "initializer": function_info['initializer'],
                        "cpu": function_info['cpu_limit'],
                        "memory": function_info['memory_limit'],
                        # "max_runtime": function_info['max_idle_time'],
                        "keepalive": function_info['max_idle_time']
                    }]
                }
                try:
                    t1 = time.time()
                    resp, _ = await asyncio.gather(self.fog_manage.send_cmd(fog_ip, cmd, timeout=None),
                                                   pull_function(function_info['code_url'],
                                                                 os.path.join('/data/functions', function_uri)))
                    # resp = await self.fog_manage.send_cmd(fog_ip, cmd, timeout=None)
                    logger.info(f'fog response {time.time() - t1}')
                    if resp['status'] == 'success':
                        logger.critical(f'{runtime_id} {resp["data"]}')
                        asyncio.get_event_loop().create_task(
                            self.fog_manage.update_container(
                                fog_ip, 'function/' + function_uri, runtime_id, resp['data'], function_info['memory_limit']))
                        with await self.redis_pool as conn:
                            await conn.execute('incr', 'function/' + function_uri)
                        data = {
                            'ip': fog_ip,
                            'runtime_id': runtime_id,
                            'keepalive': 1000
                        }
                    else:
                        status = 'fail'
                        info = resp['info']
                except Exception as e:
                    logger.error(repr(e))
                    status = 'fail'
                    info = repr(e)
            else:
                data = {
                    'ip': fog_ip,
                    'runtime_id': result_id,
                    'keepalive': 1000
                }
        except Exception as e:
            status = 'fail'
            info = repr(e)
            logger.error(repr(e))
            logger.exception('message')
            # logger.warning(self.algo.show_status())
            # logger.warning(repr(self.algo.topo.device_ip_index.items()))
        # if len(fog_nodes.keys()) != 0:
        #     key = random.choice(list(fog_nodes.keys()))
        #     reader, writer = fog_nodes[key]
        #     writer.write(packmsg(cmd))
        #     try:
        #         resp = await recvmsg(reader, timeout=3)
        #         if resp['status'] == 'success':
        #             # data = {'ip': key.split(':')[0], 'runtime_id': runtime_id}
        #             data = {'ip': key, 'runtime_id': runtime_id}
        #         else:
        #             status = 'fail'
        #             info = resp['info']
        #     except Exception as e:
        #         logger.error(repr(e))
        #         status = 'fail'
        #         info = repr(e)
        # else:
        #     status = 'fail'
        #     info = 'fog node not found'
        self.write({'status': status, 'info': info, 'data': data})


class WorkflowHandler(BaseHandler, CheckMixin):
    async def post(self):
        # test_workflow = '{"StartAt": "converter", "States": {"converter": {"Type": "Task", "Resource": "user-1/scalar1", "Next": "choice"}, "choice": {"Type": "Choice", "Choices": [{"Condition": "$.number > 80", "Next": "hot"}], "Default": "cold"}, "hot": {"Type": "Task", "Resource": "user-1/scalar1", "End": true}, "cold": {"Type": "Parallel", "Branches": [{"StartAt": "b1-converter", "States": {"b1-converter": {"Type": "Task", "Resource": "user-1/scalar1", "End": true}}}, {"StartAt": "b2-converter", "States": {"b2-converter": {"Type": "Task", "Resource": "user-1/scalar1", "End": true}}}], "End": true}}}'
        status = 'success'
        info = ''
        data = {}
        try:
            # self.json['function'] = 'scalar1'
            # workflow_uri = 'user-1/' + self.json['workflow']
            # workflow_uri = f'user-{self.current_user}/{self.json["uri"]'
            workflow_uri = self.json['workflow']
            async with self.pool.acquire() as conn:
                async with conn.cursor(aiomysql.cursors.DictCursor) as cursor:
                    await cursor.execute('SELECT * FROM `workflows` WHERE uri=%s', workflow_uri)
                    if cursor.rowcount == 0:
                        raise RuntimeError('workflow not found')
                    else:
                        workflow_info = await cursor.fetchone()

            workflow_runtime_id = os.urandom(16).hex()

            definition = json.loads(workflow_info['definition'])
            helper = WorkflowHelper(definition)
            # definition = json.loads(test_workflow)
            # helper = WorkflowHelper(definition)
            tasks = helper.all_tasks()

            for t in tasks.values():
                if function_info_cache.get(t['Resource']) is None:
                    async with self.pool.acquire() as conn:
                        async with conn.cursor(aiomysql.cursors.DictCursor) as cursor:
                            await cursor.execute('SELECT * FROM `functions` WHERE uri=%s', t['Resource'])
                            if cursor.rowcount == 0:
                                raise RuntimeError('function not found')
                            else:
                                function_info = await cursor.fetchone()
                                function_info['memory_limit'] = function_info['memory_limit'] * 1024 * 1024
                                function_info_cache[t['Resource']
                                                    ] = function_info

            results, runtime_table = helper.schedule(
                workflow_runtime_id, self.algo.schedule, self.json['ip'], function_info_cache)

            definition_with_results = json.loads(json.dumps(definition))
            results_helper = WorkflowHelper(definition_with_results)
            for k, v in results_helper.all_tasks().items():
                v['runtime'] = {'ip': results[k][0],
                                'runtime_id': results[k][1]}

            async def _wait_response(fog_ip, cmd, timeout=None):
                return await self.fog_manage.send_cmd(fog_ip, cmd, timeout)

            logger.info(runtime_table)

            wait_list = []
            schedule_list = []
            for k, v in tasks.items():
                runtime_pair = runtime_table.get(k)
                function_uri = tasks.get(k)['Resource']
                if runtime_pair[0] == runtime_pair[1]:
                    cmd = {
                        "category": "function",
                        "action": "pullup",
                        "data": [{
                            "runtime_id": runtime_pair[0],
                            "name": function_uri,
                            "image": "dx/python3:0.0.4",
                            "source": function_info_cache[function_uri]['code_url'],
                            "version": "v1.0.0",
                            "workflow": {
                                "uri": workflow_uri,
                                "runtime_id": workflow_runtime_id,
                                "role": k,
                                "definition": definition_with_results
                            },
                            "entrypoint": function_info_cache[function_uri]['handler'],
                            "initializer": function_info_cache[function_uri]['initializer'],
                            "cpu": function_info_cache[function_uri]['cpu_limit'],
                            "memory": function_info_cache[function_uri]['memory_limit'],
                            # "max_runtime": 1000,
                            "keepalive": workflow_info['max_idle_time']
                            # "keepalive": function_info_cache[function_uri]['max_idle_time']
                        }]
                    }
                    wait_list.append(pull_function(
                        function_info_cache[function_uri]['code_url'], os.path.join('/data/functions', function_uri)))
                    wait_list.append(_wait_response(results.get(k)[0], cmd))
                    schedule_list.append(k)
            try:
                t1 = time.time()
                resps = await asyncio.gather(*wait_list)
                schedule_resps = []
                logger.info(f'fog response gather: {time.time() - t1}')
                fail = False
                # logger.info(resps)
                for r in resps:
                    if r is not None:
                        if r['status'] == 'fail':
                            fail = True
                            break
                        else:
                            schedule_resps.append(r)
                if fail:
                    status = 'fail'
                    info = resps
                else:
                    for k, r in zip(schedule_list, schedule_resps):
                        function_uri = tasks.get(k)['Resource']
                        asyncio.get_event_loop().create_task(
                            self.fog_manage.update_container(
                                results.get(k)[0], workflow_runtime_id + function_uri, runtime_table.get(k)[0], r, function_info_cache.get(function_uri)['memory_limit']))
                    start_at = definition['StartAt']
                    data = {
                        'ip': results.get(start_at)[0],
                        'runtime_id': runtime_table.get(start_at)[1],
                        'keepalive': 1000
                    }
            except Exception as e:
                logger.error(e)
                logger.exception('errmsg')
                status = 'fail'
                info = repr(e)
        except Exception as e:
            status = 'fail'
            info = repr(e)
            logger.error(e)
            logger.exception('errmsg')
        self.write({'status': status, 'info': info, 'data': data})


pool = None
minio_client = None
redis_pool = None


async def mysql_init(loop):
    global pool, minio_client, redis_pool
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
        access_key='Vancior',
        secret_key='924597121',
        secure=False)
    redis_pool = await aioredis.create_pool(f'redis://{REDIS_HOST}:{REDIS_PORT}')


async def mysql_exit():
    pool.close()
    await pool.wait_closed()
    redis_pool.close()
    await redis_pool.wait_closed()


async def clock():
    while True:
        print('clock')
        await asyncio.sleep(2)


if __name__ == '__main__':
    config = {'oss_name': 'minio'}

    fog_data = FogData()
    container_data = ContainerData()
    fog_manage = FogManage('', 7000, fog_data, container_data)
    algo = FirstFitAlgo(f'/data/topos/{os.getenv("TOPO_NAME")}.topo', fog_data,
                        container_data)

    # initialize mysql
    tornado.ioloop.IOLoop.current().run_sync(lambda: mysql_init(
        asyncio.get_event_loop()))
    # create tornado application
    handlers = [(r'/deploy/function', FunctionHandler,
                 dict(
                     redis_pool=redis_pool,
                     db_pool=pool,
                     config=config,
                     algo=algo,
                     fog_manage=fog_manage)),
                (r'/deploy/workflow', WorkflowHandler,
                 dict(
                     redis_pool=redis_pool,
                     db_pool=pool,
                     config=config,
                     algo=algo,
                     fog_manage=fog_manage))]
    application = tornado.web.Application(handlers=handlers)

    application.listen(8883)
    # tornado.ioloop.IOLoop().spawn_callback(mysql_init, loop=tornado.ioloop.IOLoop().current())
    try:
        loop = asyncio.get_event_loop()
        loop.create_task(fog_manage.run())
        tornado.ioloop.IOLoop.current().start()
    except KeyboardInterrupt:
        # close mysql
        tornado.ioloop.IOLoop.current().run_sync(mysql_exit)
