from http import HTTPStatus
import click
import configparser
import http.client as client
import http.server as server
import io
import json
import os
import re
import socket
import socketserver
import sys
import traceback

from .utils import handle_exception

CONFIG = None
FUNCTION_CONTEXT = None

# TODO: 运行的log机制


def check_type(obj, *args):
    obj_type = type(obj)
    found = False
    for cls in args:
        if obj_type is cls:
            found = True
    if not found:
        raise TypeError('expect {}, get {}'.format(' or '.join(
            [cls.__name__ for cls in args]), type(obj).__name__))


class FunctionContext:
    def __init__(self):
        """ parse runtime meta info """
        self.runtime_meta = os.getenv('DX_RUNTIME')
        # print(self.runtime_meta)
        if self.runtime_meta is None:
            raise EnvironmentError('Environment variable DX_RUNTIME not found')
        self.runtime_meta = json.loads(self.runtime_meta)
        # print(self.runtime_meta)

        """ determine output """
        self.output = self.runtime_meta['output']
        try:
            if self.output is not None:
                re_match = re.match(r'http://([\d\w\.]+)(/.*)', self.output)
                host = re_match.group(1)
                self.output_residual = re_match.group(2)
                self.output_connection = client.HTTPConnection(
                    host, 80, timeout=3)
        except Exception as e:
            print(e)

        """ build execution env """
        file, function = CONFIG.get('entrypoint').split('.')
        path = CONFIG.get('function_path')
        file = os.path.join(path, file + '.py')
        if not os.path.exists(file):
            raise FileNotFoundError(f"{file} not found")

        sys.path.insert(0, path)
        mods = {'__file__': file}
        exec(compile(open(file).read(), file, 'exec'), mods, mods)
        self.function = mods.get(function)
        sys.path.pop(0)


class ForkingHTTPServer(socketserver.ForkingMixIn, server.HTTPServer):
    pass


class RuntimeHandler(server.BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'

    def run_function(self):
        try:
            if FUNCTION_CONTEXT.function is None:
                self.log_error('function not found')

            body_length = int(self.headers.get('Content-Length'))
            body_bytes = self.rfile.read(body_length)

            try:
                result = FUNCTION_CONTEXT.function(self.headers, body_bytes)
                check_type(result, bytes, tuple)
                if type(result) is bytes:
                    self.send_response(200)
                    self.end_headers()
                    self.wfile.write(result)
                elif type(result) is tuple:
                    if len(result) != 3:
                        return
                    # response code, header, data
                    code, header, data = result
                    if FUNCTION_CONTEXT.output is not None:
                        check_type(code, tuple, int, type(None))
                        check_type(header, dict)
                        check_type(data, bytes)
                        FUNCTION_CONTEXT.output_connection.request(
                            'POST', FUNCTION_CONTEXT.output_residual, body=data, headers=header)
                        """ 有时候这里会出现CannotSendRequest的错误，在http/client.py的1098行 """
                        response = FUNCTION_CONTEXT.output_connection.getresponse()
                        # body = response.read()
                        # print(response)
                        # TODO: add error handling
                        self.send_response(response.code, response.reason)
                        self.send_header('Content-Type', 'application/json')
                        """ 这里应该跳过Transfer-Encoding，否则write的数据格式也应该遵循chunked """
                        # for k, v in response.headers.items():
                        # print(k, v)
                        # if k == 'Transfer-Encoding':
                        #     continue
                        # self.send_header(k, v)
                        self.end_headers()
                        # self.flush_headers()
                        # self.wfile.write(body)
                        self.wfile.write(response.read())
                    else:
                        check_type(code, tuple, int)
                        if type(code) is tuple:
                            self.send_response(*code)
                        else:
                            self.send_response(code)
                        check_type(header, dict)
                        for key, value in header.items():
                            self.send_header(key, value)
                        self.end_headers()
                        check_type(data, bytes)
                        self.wfile.write(data)
                print('here')
            except Exception as e:
                handle_exception(self, e)

        except socket.timeout as e:
            self.log_error('Request timed out: %r', e)
            handle_exception(self, e)
        except Exception as e:
            self.log_error('error: %r', e)
            handle_exception(self, e)

    def run_test(self):
        body_length = int(self.headers.get('Content-Length'))
        try:
            body_bytes = self.rfile.read(body_length)
            # self.send_error(500, 'hhhhhhh', 'what')
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"hello":"abc"}')
        except socket.timeout as e:
            self.log_error('Request timed out: %r', e)
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
            # self.run_test()
            self.run_function()
            # mname = 'do_' + self.command
            # if not hasattr(self, mname):
            #     self.send_error(
            #         HTTPStatus.NOT_IMPLEMENTED,
            #         "Unsupported method (%r)" % self.command)
            #     return
            # method = getattr(self, mname)
            # method()
            # actually send the response if not already done.
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
    global CONFIG
    CONFIG = config_parser['DEFAULT']
    runtime_server = server.ThreadingHTTPServer(
        ('', CONFIG.getint('http_port')), RuntimeHandler)
    global FUNCTION_CONTEXT
    FUNCTION_CONTEXT = FunctionContext()
    # TODO: notify ready(send message to agent and agent set runtime_id with 'running' in redis)
    """
    data: {runtime_id: "123", ip: "172.17.0.2"}
    """
    msg = {'runtime_id': FUNCTION_CONTEXT.runtime_meta['runtime_id'],
           'ip': socket.gethostbyname(socket.gethostname())}
    # TODO: 可能的异常点，host中的ready daemon挂了
    connection = client.HTTPConnection('172.17.42.1', 10008, timeout=10)
    connection.request('POST', '/', bytes(json.dumps(msg, ensure_ascii=True),
                                          'ascii'), headers={'Content-Type': 'application/json'})
    response = connection.getresponse()
    result = json.loads(response.read())
    if result['status'] == 'success':
        runtime_server.serve_forever()
    else:
        exit(2)

#
# if __name__ == '__main__':
#     main()
