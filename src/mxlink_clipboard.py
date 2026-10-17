"""Desktop adapters and explicit headless exchange state."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

STATE = Path.home() / '.local/state/mxlink/exchange.json'
MAX_TEXT = 1024 * 1024

def graphical():
    return os.environ.get('MXLINK_HEADLESS') != '1' and bool(os.environ.get('WAYLAND_DISPLAY') or os.environ.get('DISPLAY'))

def exchange(value=None):
    if value is None:
        try:
            return json.loads(STATE.read_text())
        except (OSError, ValueError):
            return {}
    STATE.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd, name = tempfile.mkstemp(dir=STATE.parent)
    try:
        with os.fdopen(fd, 'w') as out:
            json.dump(value, out)
        os.replace(name, STATE)
    finally:
        Path(name).unlink(missing_ok=True)

def read_text():
    if not graphical():
        return exchange().get('text')
    commands = []
    if os.environ.get('WAYLAND_DISPLAY') and shutil.which('wl-paste'):
        commands.append(['wl-paste', '--no-newline', '--type', 'text'])
    if os.environ.get('DISPLAY') and shutil.which('xclip'):
        commands.append(['xclip', '-selection', 'clipboard', '-o'])
    qdbus = shutil.which('qdbus6') or shutil.which('qdbus')
    if qdbus and 'KDE' in os.environ.get('XDG_CURRENT_DESKTOP', ''):
        commands.append([qdbus, 'org.kde.klipper', '/klipper', 'getClipboardContents'])
    for command in commands:
        try:
            # A temporary file bounds memory even for large clipboard selections.
            with tempfile.TemporaryFile() as out:
                result = subprocess.run(command, stdout=out, stderr=subprocess.DEVNULL, timeout=3)
                if result.returncode or out.tell() > MAX_TEXT:
                    continue
                out.seek(0)
                text = out.read().decode('utf-8')
                if command[0] == qdbus:
                    text = text.removesuffix('\n')
                if text:
                    return text
        except (OSError, UnicodeError, subprocess.SubprocessError):
            continue
    return None

def write_text(text):
    if len(text.encode()) > MAX_TEXT:
        return None
    if not graphical():
        exchange({'text': text})
        return 'headless'
    commands = []
    if os.environ.get('WAYLAND_DISPLAY') and shutil.which('wl-copy'):
        commands.append(['wl-copy', '--type', 'text/plain;charset=utf-8'])
    if os.environ.get('DISPLAY') and shutil.which('xclip'):
        commands.append(['xclip', '-selection', 'clipboard'])
    for command in commands:
        try:
            result = subprocess.run(command, input=text.encode(), stdout=subprocess.DEVNULL,
                                    stderr=subprocess.DEVNULL, timeout=3)
            if result.returncode == 0:
                return command[0]
        except (OSError, subprocess.SubprocessError):
            continue
    return None

def file_paths():
    if not graphical():
        return [Path(p) for p in exchange().get('files', []) if Path(p).is_file()]
    from urllib.parse import urlsplit, unquote
    value = ''
    command = None
    if os.environ.get('WAYLAND_DISPLAY') and shutil.which('wl-paste'):
        command = ['wl-paste', '--no-newline', '--type', 'text/uri-list']
    elif os.environ.get('DISPLAY') and shutil.which('xclip'):
        command = ['xclip', '-selection', 'clipboard', '-t', 'text/uri-list', '-o']
    if command:
        try:
            with tempfile.TemporaryFile() as out:
                result = subprocess.run(command, stdout=out, stderr=subprocess.DEVNULL, timeout=3)
                if result.returncode == 0 and out.tell() <= MAX_TEXT:
                    out.seek(0)
                    value = out.read().decode('utf-8')
        except (OSError, UnicodeError, subprocess.SubprocessError):
            pass
    value = value or read_text() or ''
    paths = []
    for line in value.splitlines():
        if not line or line.startswith('#'):
            continue
        uri = urlsplit(line)
        if uri.scheme != 'file' or uri.netloc not in ('', 'localhost'):
            return []
        path = Path(unquote(uri.path))
        if not path.is_file():
            return []
        paths.append(path)
    return paths[:100]
