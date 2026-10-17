"""Private, expiring, one-use pairing grants shared by the two services."""
from pathlib import Path
import fcntl
import hmac
import json
import os
import secrets
import socket
import time
from urllib.parse import quote

DIRECTORY = Path.home() / '.config/mxlink'

def grant(consume=None, peek=False):
    DIRECTORY.mkdir(parents=True, exist_ok=True, mode=0o700)
    lock = os.open(DIRECTORY / 'pairing.lock', os.O_CREAT | os.O_RDWR, 0o600)
    with os.fdopen(lock, 'w') as stream:
        fcntl.flock(stream, fcntl.LOCK_EX)
        path = DIRECTORY / 'pairing.json'
        if consume is not None:
            try:
                value = json.loads(path.read_text())
            except (OSError, ValueError):
                return False
            if value['expires'] < time.time() or not hmac.compare_digest(value['code'].encode(), consume.encode()):
                return False
            if not peek:
                path.unlink()
            return True
        value = {'code': secrets.token_urlsafe(32), 'expires': time.time() + 300}
        fd = os.open(path, os.O_CREAT | os.O_TRUNC | os.O_WRONLY, 0o600)
        with os.fdopen(fd, 'w') as out:
            json.dump(value, out)
        base = 'http://' + socket.gethostname().split('.')[0] + '.local:8767'
        return {'url': base + '/setup?code=' + quote(value['code']), 'expires': value['expires']}
