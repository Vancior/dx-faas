import http.client
import json
import logging
import os
import socket
from datetime import datetime, timedelta

DEFAULT_TIMEOUT = 50
# CLOUD_HOST = '127.0.0.1'
CLOUD_HOST = os.getenv('CLOUD_HOST')
CLOUD_PORT = int(os.getenv('CLOUD_PORT'))
MY_IP = os.getenv('MY_IP')
assert CLOUD_HOST is not None
logger = logging.getLogger('Function Service')


class FunctionNotRegisterError(Exception):
    def __init__(self, function_uri):
        super().__init__(f'function {function_uri} not registered')


class FunctionExpireError(Exception):
    def __init__(self, function_uri):
        super().__init__(f'function {function_uri} expired')


class FunctionRequestTimeout(Exception):
    def __init__(self, function_uri):
        super().__init__(f'timeout when requesting function {function_uri}')


class FunctionNotFound(Exception):
    def __init__(self, function_uri):
        super().__init__(f'function {function_uri} not found')


class RequestError(Exception):
    def __init__(self, msg=''):
        super().__init__(msg)


class FunctionService:
    def __init__(self, token_manager, timeout=DEFAULT_TIMEOUT):
        self.token_manager = token_manager
        self.timeout = timeout
        self.function_table = dict()

    def request(self, function_uri, workflow=False):
        """
        Error: FunctionRequestTimeout, OSError
        """
        try:
            cloud_connection = http.client.HTTPConnection(
                CLOUD_HOST, port=CLOUD_PORT, timeout=DEFAULT_TIMEOUT)
            if function_uri in self.function_table:
                logger.warning(f'overriding {function_uri}')

            if workflow:
                postData = json.dumps({
                    'ip': MY_IP,
                    'workflow': function_uri,
                    'token': self.token_manager.get_token()
                })
                postURL = '/deploy/workflow'
            else:
                postData = json.dumps({
                    'ip': MY_IP,
                    'function': function_uri,
                    'token': self.token_manager.get_token()
                })
                postURL = '/deploy/function'
            cloud_connection.request(
                'POST',
                postURL,
                body=postData,
                headers={'Content-Type': 'application/json'})
            response = cloud_connection.getresponse()
            if response.status != 200:
                raise RequestError(f'{response.status} {response.reason}')
            data = json.loads(response.read())
            logger.info(json.dumps(data))
            if data['status'] == 'fail':
                raise RequestError(f'{data["info"]}')
            # keys of data: node_ip, keepalive, runtime_id
            data = data['data']
            connection = http.client.HTTPConnection(
                data['ip'], port=80, timeout=self.timeout)
            self.function_table[function_uri] = {
                'ip': data['ip'],
                'connection': connection,
                'runtime_id': data['runtime_id'],
                'keepalive': data['keepalive'],
                # 'keepalive': 1000,
                'last_visit': datetime.now()
            }
            cloud_connection.close()
        except socket.timeout as e:
            raise e
            # raise FunctionRequestTimeout(function_uri)

    def call(self, function_uri, data=None, record_id=None, headers=None):
        """
        Error: FunctionNotRegisterError, FunctionExpireError, RequestError
        """
        if function_uri not in self.function_table:
            raise FunctionNotRegisterError(function_uri)

        entry = self.function_table[function_uri]
        if datetime.now() - entry['last_visit'] > timedelta(minutes=entry['keepalive']):
            raise FunctionExpireError(function_uri)

        # try:
        post_data = bytes(json.dumps({'recordId': record_id, 'data': data}, ensure_ascii=False), encoding='utf-8')
        entry['connection'].request('POST', f"/{entry['runtime_id']}",
                                    post_data, headers)
        response = entry['connection'].getresponse()
        entry['last_visit'] = datetime.now()
        return response.read(), response.getheaders()
        # except TypeError:
        #     raise RequestError()

    def get_ip(self, function_uri):
        if self.function_table.get(function_uri) is None:
            return None
        return self.function_table.get(function_uri)['ip']
