#!/usr/bin/env python3

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
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
import re
import socket

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
    "4550a09c4c964894a4679a28455b921d"
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
            supplied,
            TOKEN
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


class Handler(BaseHTTPRequestHandler):

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
        # L'appairage utilise toujours le nom mDNS stable,
        # indépendamment de l'adresse utilisée pour ouvrir cette page.
        base_url = f"http://{MDNS_HOST}:{PORT}"

        payload = (
            "MXLINKPAIR:"
            + json.dumps(
                {
                    "version": 1,
                    "name": "MXBook",
                    "base_url": base_url,
                    "token": TOKEN,
                },
                ensure_ascii=False,
                separators=(",", ":"),
            )
        )

        pair_url = (
            "shortcuts://run-shortcut"
            "?name=" + quote("MX Link", safe="")
            + "&input=text"
            + "&text=" + quote(payload, safe="")
        )

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

a.button {{
    display: block;
    box-sizing: border-box;
    width: 100%;
    padding: 17px 18px;
    margin: 10px 0;
    border-radius: 14px;
    text-align: center;
    text-decoration: none;
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

<a class="button pair"
   href="{html.escape(pair_url, quote=True)}">
Appairer cet iPhone
</a>

<div class="note">
MX Link communique directement avec cet ordinateur
sur votre réseau local.
</div>

</main>
</body>
</html>
"""

        self.send_bytes(
            200,
            page.encode("utf-8"),
            "text/html; charset=utf-8"
        )

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

        length = int(
            self.headers.get(
                "Content-Length",
                "0"
            ) or "0"
        )

        conn = http.client.HTTPConnection(
            BACKEND_HOST,
            BACKEND_PORT,
            timeout=300
        )

        conn.putrequest(
            self.command,
            target
        )

        for header in (
            "Content-Type",
            "Content-Disposition",
            "Accept",
            "User-Agent",
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
                break

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

        self.proxy()

    def do_POST(self):
        self.proxy()

    def log_message(
        self,
        fmt,
        *args
    ):
        pass


server = ThreadingHTTPServer(
    (HOST, PORT),
    Handler
)

server.serve_forever()
