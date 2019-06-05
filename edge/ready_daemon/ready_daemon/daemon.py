import argparse
import http.server
import json
import redis

# redis_client = redis.Redis()
redis_client = None


def get_meta():
    redis_host = os.getenv('REDIS_HOST', '127.0.0.1')
    redis_port = os.getenv('REDIS_PORT', 6379)
    return {'redis_host': redis_host, 'redis_port': redis_port}


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--redis-host', default='127.0.0.1')
    parser.add_argument('--redis-port', type=int, default=6379)
    return parser.parse_args()


class ReadyHandler(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        """
        data: {runtime_id:"123", ip: "172.17.0.2"}
        """
        length = int(self.headers.get('Content-Length'))
        data = self.rfile.read(length)
        print(data)
        data = json.loads(data)
        redis_client.mset({f"{data['runtime_id']}:status": 'running',
                           f"{data['runtime_id']}:ip": data['ip']})
        response = {'status': 'success'}
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(
            bytes(json.dumps(response, ensure_ascii=True), encoding='ascii'))


def run():
    global redis_client
    # meta = get_meta()
    args = parse_args()
    redis_client = redis.Redis(
        host=args.redis_host, port=args.redis_port)
    with http.server.ThreadingHTTPServer(('', 10008), ReadyHandler) as server:
        server.serve_forever()
