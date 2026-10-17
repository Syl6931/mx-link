#!/usr/bin/env python3
"""Local user interface, also usable over SSH without Plasma."""
import argparse
import json
from pathlib import Path
import subprocess
import shutil
import sys
from urllib.request import Request, urlopen
import mxlink_clipboard as clipboard

parser = argparse.ArgumentParser(description=__doc__)
sub = parser.add_subparsers(dest='command', required=True)
sub.add_parser('pair', help='Create a five-minute, single-use pairing link')
sub.add_parser('status')
sub.add_parser('get-text', help='Read the desktop clipboard or headless exchange text')
sub.add_parser('set-text', help='Read text from stdin')
p = sub.add_parser('send-files', help='Expose files to the iPhone in headless mode')
p.add_argument('paths', nargs='+')
sub.add_parser('config', help='Show reception settings')
p = sub.add_parser('set-config', help='Apply a JSON object from stdin')
args = parser.parse_args()
try:
    if args.command == 'get-text':
        print(clipboard.read_text() or '', end='')
    elif args.command == 'set-text':
        text = sys.stdin.buffer.read(clipboard.MAX_TEXT + 1).decode()
        if not clipboard.write_text(text):
            raise ValueError('Clipboard unavailable or text too large')
    elif args.command == 'send-files':
        if clipboard.graphical():
            raise ValueError('Use your file manager clipboard in a desktop session')
        paths = [Path(p).resolve(strict=True) for p in args.paths]
        if len(paths) > 100 or not all(p.is_file() for p in paths):
            raise ValueError('Select at most 100 regular files')
        clipboard.exchange({'files': [str(p) for p in paths]})
    else:
        endpoint = {'pair': 'pairing/start', 'status': 'state', 'config': 'config', 'set-config': 'config'}[args.command]
        data = b'{}' if args.command == 'pair' else None
        if args.command == 'set-config':
            data = sys.stdin.buffer.read(clipboard.MAX_TEXT + 1)
        req = Request('http://127.0.0.1:8765/' + endpoint, data=data,
                      headers={'Content-Type': 'application/json'})
        with urlopen(req, timeout=10) as response:
            result = json.load(response)
        if args.command == 'pair':
            print(result['url'])
            print('Valid 5 minutes, one opening. Keep this link private.')
            if shutil.which('qrencode'):
                subprocess.run(['qrencode', '-t', 'ANSIUTF8', result['url']], check=True)
        else:
            print(json.dumps(result, ensure_ascii=False, indent=2))
except Exception as exc:
    parser.exit(1, f'MX Link: {exc}\n')
