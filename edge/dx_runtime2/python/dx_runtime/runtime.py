from http import HTTPStatus
import click
import configparser
import http.client
import http.server
import io
import json
import logging
import os
import re
import socket
import socketserver
import sys
import traceback

from .executor import Executor
from .utils import handle_exception

import multiprocessing

# TODO: 运行的log机制


class FunctionContext:
    def __init__(self, config):
        """ parse runtime meta info """
        self.runtime_meta = os.getenv('DX_RUNTIME')
        self.host_ip = os.getenv('HOST_IP')
        if self.runtime_meta is None:
            raise EnvironmentError('Environment variable DX_RUNTIME not found')
        self.runtime_meta = json.loads(self.runtime_meta)

        """ determine output """
        self.output = self.runtime_meta['output']
        try:
            if self.output is not None:
                re_match = re.match(r'http://([\d\w\.]+)(/.*)', self.output)
                host = re_match.group(1)
                # self.output_residual = re_match.group(2)
                self.host = host
                self.url = re_match.group(2)
                # self.output_connection = http.client.HTTPConnection(
                #     host, 80, timeout=3)
        except Exception as e:
            print(e)

        """ build execution env """
        file, function = config.get('entrypoint').split('.')
        path = config.get('function_path')
        file = os.path.join(path, file + '.py')
        if not os.path.exists(file):
            raise FileNotFoundError(f"{file} not found")
        self.path = path
        self.file = file
        self.function = function
        # sys.path.insert(0, path)
        # mods = {'__file__': file}
        # exec(compile(open(file).read(), file, 'exec'), mods, mods)
        # self.function = mods.get(function)
        # sys.path.pop(0)


def check_type(obj, *args):
    obj_type = type(obj)
    found = False
    for cls in args:
        if obj_type is cls:
            found = True
    if not found:
        raise TypeError('expect {}, get {}'.format(' or '.join(
            [cls.__name__ for cls in args]), type(obj).__name__))


executor = None


def test():
    print('test')
    return 123


class RuntimeHandler(http.server.BaseHTTPRequestHandler):
    # protocol_version = 'HTTP/1.1'

    def run_function(self):
        try:
            # get is function from email.message.Message, and lowering is done inside
            body_length = int(self.headers.get('Content-Length'))
            body_bytes = self.rfile.read(body_length)
            executor.enqueue(self.headers.items(), body_bytes)
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(
                bytes(json.dumps({'status': 'success'}), encoding='ascii'))
        except socket.timeout as e:
            self.log_error('Request timed out: %r', e)
            handle_exception(self, e)
        except Exception as e:
            self.log_error('error: %r', e)
            handle_exception(self, e)

    def handle_one_request(self):
        """Handle a single HTTP request.
        override parent method, which is warned
        """
        try:
            self.raw_requestline = self.rfile.readline(65537)
            if len(self.raw_requestline) > 65536:
                self.requestline = ''
                self.request_version = ''
                self.command = ''
                self.send_error(HTTPStatus.REQUEST_URI_TOO_LONG)
                return
            if not self.raw_requestline:
                self.close_connection = True
                return
            if not self.parse_request():
                # An error code has been sent, just exit
                return
            self.run_function()
            self.wfile.flush()
        except socket.timeout as e:
            # a read or a write timed out.  Discard this connection
            self.log_error("Request timed out: %r", e)
            self.close_connection = True
            return


@click.command()
@click.argument('entrypoint')
@click.option('--port', type=int, default=80)
def main(entrypoint, port):
    config_parser = configparser.ConfigParser()
    config_parser['DEFAULT'] = dict(
        http_port=str(port),
        function_path='/data/function'
        # http_port=10010,
        # function_path='/home/vancior/Documents/senior/functions/test2'
    )
    config_parser['DEFAULT']['entrypoint'] = entrypoint
    config = config_parser['DEFAULT']

    context = FunctionContext(config)
    if context.function is None:
        logging.error('Function not found')
        exit(1)

    global executor
    executor = Executor(config, context)

    runtime_server = http.server.ThreadingHTTPServer(
        ('', config.getint('http_port')), RuntimeHandler)

    """
    send ready message
    data: {runtime_id: "123", ip: "172.17.0.2"}
    """
    msg = {'runtime_id': context.runtime_meta['runtime_id'],
           'ip': socket.gethostbyname(socket.gethostname())}
    # TODO: 可能的异常点，host中的ready daemon挂了
    connection = http.client.HTTPConnection(context.host_ip, 10008, timeout=10)
    connection.request('POST', '/', bytes(json.dumps(msg, ensure_ascii=True),
                                          'ascii'), headers={'Content-Type': 'application/json'})
    response = connection.getresponse()
    result = json.loads(response.read())
    if result['status'] == 'success':
        runtime_server.serve_forever()
    else:
        exit(2)
    runtime_server.serve_forever()
