import http.server
import io
import json
import traceback


def handle_exception(request_handler: http.server.BaseHTTPRequestHandler, e: Exception) -> None:
    io_traceback = io.StringIO()
    traceback.print_tb(e.__traceback__, file=io_traceback)

    request_handler.send_response(500)
    request_handler.send_header('Content-type', 'application/json')
    request_handler.end_headers()
    request_handler.wfile.write(bytes(json.dumps({'error': repr(
        e), 'traceback': io_traceback.getvalue()}, ensure_ascii=True), encoding='ascii'))
