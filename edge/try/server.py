from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pprint import pprint

class MyHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        pprint(self.headers.__dict__)
        pprint(self.request)
        pprint(self.requestline)

    def do_POST(self):
        pprint(self.headers.__dict__)
        pprint(self.request)
        pprint(self.requestline)
        length = int(self.headers.get('Content-Length'))
        data = self.rfile.read(length)
        pprint(data)
    
    # def handle_one_request(self):
        # while True:
        # data = self.rfile.read(65537)
        # if data and len(data) > 0:
        #     pprint(data)
        # else:
        #     break


if __name__ == '__main__':
    httpd = ThreadingHTTPServer(('', 8000), MyHandler)
    httpd.serve_forever()