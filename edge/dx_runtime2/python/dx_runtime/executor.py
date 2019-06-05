import http.client
import json
import multiprocessing as mp
import os
import pickle
import re
import sys
import threading
import time
import traceback

from pprint import pprint


def run(context, headers, body_bytes):
    try:
        sys.path.insert(0, context.path)
        mods = {'__file__': context.file}
        exec(compile(open(context.file).read(),
                     context.file, 'exec'), mods, mods)
        function = mods.get(context.function)
        sys.path.pop(0)
        result = function(headers, body_bytes)
        code, headers, data = result
        # connection = http.client.HTTPConnection('172.17.42.1', 8080)
        # connection.request('POST', '/', data, headers=headers)
        # response = connection.getresponse()
        print(f"{context.runtime_meta['runtime_id']}: {data}")
        connection = http.client.HTTPConnection(context.host, 80)
        connection.request('POST', context.url, data, headers={'Content-Type': 'application/octet-stream'})
        response = json.loads(connection.getresponse().read())
        if response['status'] != 'success':
            raise RuntimeError(response['error'])
    except Exception as e:
        connection = http.client.HTTPConnection('172.17.42.1', 8080)
        connection.request('POST', '/', bytes(json.dumps({'status': 'fail', 'error': repr(e), 'traceback': traceback.format_tb(
            e.__traceback__)}), encoding='ascii'), headers={'Content-Type': 'application/json'})
        response = connection.getresponse()


def post_process(result):
    print(result)
    code, headers, data = result
    connection = http.client.HTTPConnection('172.17.42.1', 8080)
    connection.request('POST', '/', data, headers=headers)
    response = connection.getresponse()


def error_callback(result):
    print(result)
    traceback.print_tb(result.__traceback__)
    connection = http.client.HTTPConnection('172.17.42.1', 8080)
    connection.request('POST', '/', pickle.dumps(repr(result)))
    response = connection.getresponse()


def test():
    print('test')
    return 123


class Master:

    def clean(self):
        while True:
            self.clean_lock.acquire()
            new_workers = []
            for worker in self.workers:
                if worker.is_alive():
                    new_workers.append(worker)
                else:
                    worker.join()
                    print('join worker {}'.format(id(worker)))
            self.workers = new_workers
            # self.workers = [
            #     worker for worker in self.workers if worker.is_alive()]
            self.clean_lock.release()
            time.sleep(1)

    def __init__(self, config, context):
        # self.pool = mp.Pool(os.cpu_count() - 1)
        self.config = config
        self.context = context
        self.workers = []
        self.clean_lock = threading.Lock()
        self.clean_thread = threading.Thread(target=self.clean)
        self.clean_thread.start()

    def run(self, headers, body_bytes):
        self.clean_lock.acquire()
        worker = mp.Process(target=run, args=(
            self.context, headers, body_bytes))
        self.workers.append(worker)
        worker.start()
        self.clean_lock.release()
        # self.pool.apply_async(run, args=(self.context, headers, body_bytes), kwds=dict(),
        #                       callback=post_process, error_callback=error_callback).get(1)


def listen(pipe, config, context):
    master = Master(config, context)
    while True:
        data = pipe.recv()
        master.run(*data)


class Executor:
    def __init__(self, config, context):
        # self.pool = mp.Pool(os.cpu_count() - 1)
        # self.config = config
        # self.context = context
        a_conn, b_conn = mp.Pipe(duplex=False)
        self.master = mp.Process(target=listen, args=(a_conn, config, context))
        self.pipe = b_conn
        self.master.start()
        a_conn.close()

    def enqueue(self, headers, body_bytes):
        # try:
        print(body_bytes)
        self.pipe.send((headers, body_bytes))
        # connection = http.client.HTTPConnection('172.17.42.1', 8080)
        # headers_map = {}
        # for k, v in headers:
        #     headers_map[k] = v
        # connection.request('POST', '/', body_bytes, headers=headers_map)
        # response = connection.getresponse()
        # print(response.read())
        # self.pool.apply_async(_test).get(5)
        # print(self.pool.apply(test))
        # self.pool.apply_async(_test, args=tuple(), kwds={}, callback=post_process, error_callback=error_callback).get(5)
        # self.pool.apply_async(run, args=(self.context, headers, body_bytes), kwds=dict(),
        #                       callback=post_process, error_callback=error_callback)
        # except Exception as e:
        #     print(e)
        #     traceback.print_tb(e.__traceback__)
        # error_callback(e)
