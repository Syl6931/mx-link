#!/usr/bin/env python3

from urllib.parse import (
    urlsplit,
    parse_qsl,
    urlencode,
    quote,
    urlunsplit,
)
from pathlib import Path
import http.client
import html
import hmac
import json
import socket
from mxlink_http import SafeHandler, BoundedServer, MAX_UPLOAD, MAX_JSON
from mxlink_pairing import grant

HOST = "0.0.0.0"
PORT = 8767

MDNS_HOST = (
    socket.gethostname()
    .split(".")[0]
    + ".local"
)

BACKEND_HOST = "127.0.0.1"
BACKEND_PORT = 8765

SHORTCUT_URL = (
    "https://www.icloud.com/shortcuts/"
    "cc0988746b2f4add8c9578299107c4ae"
)

TOKEN = (
    Path.home()
    / ".config"
    / "mxlink"
    / "token"
).read_text(encoding="utf-8").strip()


def authenticated_path(raw_path, authorization):
    parts = urlsplit(raw_path)

    params = parse_qsl(
        parts.query,
        keep_blank_values=True
    )

    supplied = None
    kept = []

    for key, value in params:
        if key in ("key", "token"):
            if supplied is None:
                supplied = value
        else:
            kept.append((key, value))

    if supplied is None and authorization:
        prefix = "Bearer "

        if authorization.startswith(prefix):
            supplied = authorization[len(prefix):].strip()

    valid = (
        supplied is not None
        and hmac.compare_digest(
            supplied.encode("utf-8"),
            TOKEN.encode("utf-8")
        )
    )

    clean_path = urlunsplit((
        "",
        "",
        parts.path or "/",
        urlencode(kept, doseq=True),
        ""
    ))

    return valid, clean_path


class Handler(SafeHandler):

    protocol_version = "HTTP/1.1"

    def send_bytes(
        self,
        status,
        body,
        content_type="text/plain; charset=utf-8"
    ):
        self.send_response(status)
        self.send_header(
            "Content-Type",
            content_type
        )
        self.send_header(
            "Content-Length",
            str(len(body))
        )
        self.send_header(
            "Connection",
            "close"
        )
        self.end_headers()
        self.wfile.write(body)

    def setup_page(self):
        code = dict(parse_qsl(urlsplit(self.path).query)).get("code", "")
        if not code or not grant(consume=code, peek=True):
            self.send_bytes(403, b"Open a new pairing window from MX Link or mxlink pair.")
            return

        page = f"""<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport"
      content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>MX Link</title>

<style>
body {{
    margin: 0;
    padding: 32px 22px;
    font-family: -apple-system, BlinkMacSystemFont, sans-serif;
    background: #111;
    color: #fff;
}}

main {{
    max-width: 520px;
    margin: 0 auto;
}}

h1 {{
    margin: 16px 0 8px;
    font-size: 34px;
}}

.subtitle {{
    color: #aaa;
    margin-bottom: 34px;
    line-height: 1.45;
}}

.step {{
    margin: 28px 0 10px;
    font-weight: 700;
}}

.button {{
    display: block;
    box-sizing: border-box;
    width: 100%;
    padding: 17px 18px;
    margin: 10px 0;
    border-radius: 14px;
    text-align: center;
    text-decoration: none;
    border: 0;
    cursor: pointer;
    font-family: inherit;
    font-size: 18px;
    font-weight: 700;
}}

.install {{
    background: #fff;
    color: #111;
}}

.pair {{
    background: #327cff;
    color: white;
}}

.note {{
    margin-top: 28px;
    color: #999;
    font-size: 14px;
    line-height: 1.45;
}}

.ok {{
    font-size: 46px;
}}
</style>
</head>

<body>
<main>

<div class="ok">↔</div>

<h1>MX Link</h1>

<div class="subtitle">
Reliez cet iPhone à votre MXBook.
Deux étapes, puis MX Link est prêt.
</div>

<div class="step">1. Installer le raccourci</div>

<a class="button install"
   href="{html.escape(SHORTCUT_URL, quote=True)}">
Installer MX Link
</a>

<div class="step">2. Revenir ici puis appairer</div>

<form method="post" action="/setup/pair?code={html.escape(code, quote=True)}">
<button class="button pair" type="submit">
Appairer cet iPhone
</button>
</form>

<div class="note">
MX Link communique directement avec cet ordinateur
sur votre réseau local.
</div>

</main>
</body>
</html>
"""

        self.send_bytes(200, page.encode("utf-8"), "text/html; charset=utf-8")

    def complete_pairing(self):
        code = dict(parse_qsl(urlsplit(self.path).query)).get("code", "")
        if not code or not grant(consume=code):
            self.send_bytes(403, b"Open a new pairing window from MX Link or mxlink pair.")
            return

        # A single click redirects into Shortcuts; no second HTML page.
        base_url = f"http://{MDNS_HOST}:{PORT}"
        payload = "MXLINKPAIR:" + json.dumps(
            {
                "version": 1,
                "name": socket.gethostname().split(".")[0],
                "base_url": base_url,
                "token": TOKEN,
            },
            ensure_ascii=False,
            separators=(",", ":"),
        )
        pair_url = (
            "shortcuts://run-shortcut"
            "?name=" + quote("MX Link", safe="")
            + "&input=text"
            + "&text=" + quote(payload, safe="")
        )
        self.send_response(303)
        self.send_header("Location", pair_url)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def reject(self):
        self.send_bytes(
            401,
            b"Unauthorized"
        )

    def proxy(self):
        ok, target = authenticated_path(
            self.path,
            self.headers.get("Authorization")
        )

        if not ok:
            self.reject()
            return

        allowed = {
            "GET": {"/health", "/clipboard", "/clipboard/type", "/clipboard/raw",
                    "/clipboard/manifest", "/clipboard/item"},
            "POST": {"/", "/upload"},
        }
        if urlsplit(target).path not in allowed.get(self.command, set()):
            self.send_bytes(404, b"Not found")
            return
        length = 0
        if self.command == "POST":
            length = self.body_length(MAX_UPLOAD if urlsplit(target).path == "/upload" else MAX_JSON)
            if length is None:
                return

        conn = http.client.HTTPConnection(
            BACKEND_HOST,
            BACKEND_PORT,
            timeout=300
        )

        try:
            conn.putrequest(
                self.command,
                target
            )

            for header in (
                "Content-Type",
                "Content-Disposition",
                "Accept",
                "User-Agent",
                "X-MX-Filename",
            ):
                value = self.headers.get(header)

                if value:
                    conn.putheader(
                        header,
                        value
                    )

            if length:
                conn.putheader(
                    "Content-Length",
                    str(length)
                )

            conn.endheaders()

            remaining = length

            while remaining > 0:
                chunk = self.rfile.read(
                    min(
                        1024 * 1024,
                        remaining
                    )
                )

                if not chunk:
                    self.send_bytes(400, b"Incomplete body")
                    return

                conn.send(chunk)
                remaining -= len(chunk)

            response = conn.getresponse()

            self.send_response(
                response.status
            )

            for header in (
                "Content-Type",
                "Content-Length",
                "Content-Disposition",
            ):
                value = response.getheader(
                    header
                )

                if value:
                    self.send_header(
                        header,
                        value
                    )

            self.send_header(
                "Connection",
                "close"
            )

            self.end_headers()

            while True:
                chunk = response.read(
                    1024 * 1024
                )

                if not chunk:
                    break

                self.wfile.write(chunk)

        finally:
            conn.close()

    def do_GET(self):
        path = urlsplit(
            self.path
        ).path

        if path in ("/", "/setup"):
            self.setup_page()
            return

        if path == "/setup/health":
            self.send_bytes(
                200,
                b"MX Link Setup OK"
            )
            return

        try:
            self.proxy()
        except (OSError, http.client.HTTPException):
            self.close_connection = True

    def do_POST(self):
        if urlsplit(self.path).path == "/setup/pair":
            length = self.body_length(1024)
            if length is not None:
                self.rfile.read(length)
                self.complete_pairing()
            return
        try:
            self.proxy()
        except (OSError, http.client.HTTPException):
            self.close_connection = True

    def log_message(
        self,
        fmt,
        *args
    ):
        pass


if __name__ == "__main__":
    with BoundedServer((HOST, PORT), Handler) as server:
        server.serve_forever()
