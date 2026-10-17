"""Shared bounded HTTP handling; no request URLs or credentials in logs."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import threading

MAX_UPLOAD = 500 * 1024 * 1024
MAX_JSON = 1024 * 1024

class BoundedServer(ThreadingHTTPServer):
    daemon_threads = True
    def __init__(self, *args, **kwargs):
        self.slots = threading.BoundedSemaphore(8)
        super().__init__(*args, **kwargs)

    def process_request(self, request, address):
        if not self.slots.acquire(blocking=False):
            request.close()
            return
        try:
            super().process_request(request, address)
        except Exception:
            self.slots.release()
            raise

    def process_request_thread(self, request, address):
        try:
            super().process_request_thread(request, address)
        finally:
            self.slots.release()

class SafeHandler(BaseHTTPRequestHandler):
    def setup(self):
        super().setup()
        self.connection.settimeout(30)

    def end_headers(self):
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Referrer-Policy', 'no-referrer')
        self.send_header('X-Frame-Options', 'DENY')
        self.send_header('Connection', 'close')
        self.close_connection = True
        super().end_headers()

    def body_length(self, maximum):
        values = self.headers.get_all('Content-Length', [])
        if self.headers.get('Transfer-Encoding') or len(values) != 1:
            self.send_error(400, 'One Content-Length required; chunked unsupported')
            return None
        value = values[0]
        if len(value) > 12 or not value.isascii() or not value.isdecimal():
            self.send_error(400, 'Invalid Content-Length')
            return None
        length = int(value)
        if length > maximum:
            self.send_error(413, 'Payload too large')
            return None
        return length

    def log_message(self, *args):
        pass
