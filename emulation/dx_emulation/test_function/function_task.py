import http.server
import json
import logging
import socketserver
import time

from dx_emulation.utils import TokenManager, FunctionService

logger = logging.getLogger('Test-Function')


class ServiceContext:
    def __init__(self):
        self.token_manager = TokenManager()
        self.function_service = FunctionService(
            self.token_manager, timeout=None)

    def request(self, name, is_workflow=False):
        self.function_service.request(name, workflow=is_workflow)

    def call(self, name, data, headers=None, record_id=None):
        if headers is None:
            headers = {'Content-Type': 'application/json'}
        if not isinstance(data, str) and not isinstance(data, bytes):
            data = json.dumps(data)
        data = json.dumps(json.loads(data), ensure_ascii=False)
        return self.function_service.call(name, data=data, headers=headers, record_id=record_id)


context = ServiceContext()


class TestFunctionHandler(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get('Content-Length'))
        print(length)
        req = json.loads(self.rfile.read(length))
        print(req)
        if req['type'] == 'function':
            workflow = False
        else:
            workflow = True
        t1 = time.time()
        try:
            context.request(req['name'], is_workflow=workflow)
            # if workflow:
            #     tmp = json.loads(req['data'])
            #     tmp['recordId'] = req['record_id']
            #     req['data'] = json.dumps(tmp)
            if workflow:
                body, headers = context.call(req['name'], data=req['data'], record_id=req['record_id'])
            else:
                body, headers = context.call(req['name'], data=req['data'])
            t1 = int((time.time() - t1) * 1000)
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(bytes(json.dumps(
                {'status': 'success', 'time': t1, 'ip': context.function_service.get_ip(req['name']), 'data': json.loads(body.decode('utf-8'))}, ensure_ascii=False), encoding='utf-8'))
        except Exception as e:
            logger.error(e)
            logger.exception('errmsg')
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(bytes(json.dumps(
                {'status': 'fail', 'info': repr(e)}, ensure_ascii=False), encoding='utf-8'))


def run():
    with socketserver.ThreadingTCPServer(('', 6007), TestFunctionHandler) as httpd:
        logger.info('listening on 0.0.0.0:6007')
        httpd.serve_forever()
