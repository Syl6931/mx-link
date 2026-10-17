"""Exercise real HTTP services with a fresh HOME and no graphical environment."""
import http.client
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
import unittest
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]

class IntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory(prefix='mxlink-integration-')
        cls.home = Path(cls.tmp.name)
        cls.env = dict(os.environ, HOME=str(cls.home))
        for key in ('DISPLAY', 'WAYLAND_DISPLAY', 'DBUS_SESSION_BUS_ADDRESS'):
            cls.env.pop(key, None)
        config = cls.home / '.config/mxlink'
        config.mkdir(parents=True)
        (config / 'token').write_text('test-secret-only')
        (config / 'config.json').write_text(json.dumps({'receive_dir': str(cls.home / 'received')}))
        # Never terminate another application that owns these ports.
        for port in (8765, 8767):
            with socket.socket() as sock:
                try:
                    sock.bind(('127.0.0.1', port))
                except OSError:
                    raise unittest.SkipTest('Integration ports already in use')
        cls.log = open(cls.home / 'test.log', 'w')
        cls.processes = [subprocess.Popen([sys.executable, str(ROOT / 'src' / name)],
                         env=cls.env, stdout=cls.log, stderr=cls.log)
                         for name in ('mxlink.py', 'mxlink-http-gateway.py')]
        for _ in range(100):
            try:
                conn = http.client.HTTPConnection('127.0.0.1', 8767, timeout=.2)
                conn.request('GET', '/setup/health')
                if conn.getresponse().status == 200:
                    conn.close()
                    backend = http.client.HTTPConnection('127.0.0.1', 8765, timeout=.2)
                    backend.request('GET', '/health')
                    ready = backend.getresponse().status == 200
                    backend.close()
                    if ready:
                        return
            except OSError:
                time.sleep(.05)
        for process in cls.processes:
            process.terminate(); process.wait(timeout=5)
        cls.log.close()
        raise RuntimeError('Services did not start: ' + (cls.home/'test.log').read_text())

    @classmethod
    def tearDownClass(cls):
        for process in cls.processes:
            process.terminate()
            process.wait(timeout=5)
        cls.log.close()
        cls.tmp.cleanup()

    def request(self, method, path, body=None, headers=None, port=8767):
        conn = http.client.HTTPConnection('127.0.0.1', port, timeout=5)
        conn.request(method, path, body, headers if headers is not None else ({"Content-Type":"application/json"} if method == "POST" else {}))
        response = conn.getresponse()
        result = response.status, response.read(), dict(response.getheaders())
        conn.close()
        return result

    def test_authentication_and_local_only_routes(self):
        self.assertEqual(self.request('GET', '/health')[0], 401)
        self.assertEqual(self.request('GET', '/health?key=wrong')[0], 401)
        self.assertEqual(self.request('GET', '/health', headers={'Authorization':'Bearer test-secret-only'})[0], 200)
        for path in ('/config', '/state', '/history', '/openers', '/mxlink-ca.cer', '/status'):
            self.assertEqual(self.request('GET', path+'?key=test-secret-only')[0], 404)
        for path in ('/config', '/pairing/start', '/history/clear', '/open-folder'):
            self.assertEqual(self.request('POST', path+'?key=test-secret-only', b'{}')[0], 404)
        self.assertEqual(self.request('POST', '/config', b'{}', {'Origin':'http://evil.test'}, 8765)[0], 403)
        self.assertEqual(self.request('GET', '/config', headers={'Host':'evil.test:8765'}, port=8765)[0], 403)

    def test_pairing_one_use_and_expiry(self):
        self.assertEqual(self.request('GET', '/setup')[0], 403)
        result = self.request('POST', '/pairing/start', b'{}', port=8765)
        grant = json.loads(result[1]); url = urlsplit(grant['url'])
        setup = url.path + '?' + url.query
        status, body, headers = self.request('GET', setup)
        self.assertEqual(status, 200)
        self.assertNotIn(b'test-secret-only', body)
        self.assertEqual(headers['Cache-Control'], 'no-store')
        self.assertEqual(body.count(b'Installer MX Link'), 1)
        self.assertEqual(body.count(b'Appairer cet iPhone'), 1)
        self.assertNotIn('Préparer l’appairage'.encode(), body)
        self.assertIn(b'<form method="post" action="/setup/pair?', body)
        redeem = '/setup/pair?' + url.query
        self.assertEqual(self.request('GET', redeem)[0], 401)
        first = self.request('POST', redeem, b'')
        self.assertEqual(first[0], 303)
        self.assertEqual(first[1], b'')
        self.assertTrue(first[2]['Location'].startswith('shortcuts://run-shortcut?'))
        self.assertIn('MXLINKPAIR%3A', first[2]['Location'])
        self.assertIn('test-secret-only', first[2]['Location'])
        self.assertEqual(first[2]['Cache-Control'], 'no-store')
        self.assertEqual(self.request('POST', redeem, b'')[0], 403)
        second = json.loads(self.request('POST', '/pairing/start', b'{}', port=8765)[1])
        path = self.home / '.config/mxlink/pairing.json'
        data = json.loads(path.read_text()); data['expires'] = 0; path.write_text(json.dumps(data))
        self.assertEqual(self.request('GET', '/setup?' + urlsplit(second['url']).query)[0], 403)

    def test_headless_text_and_files(self):
        payload = json.dumps({'text':'bonjour — privé'}).encode()
        self.assertEqual(self.request('POST', '/?key=test-secret-only', payload, {'Content-Type':'application/json'})[0], 200)
        self.assertEqual(self.request('GET', '/clipboard/raw?key=test-secret-only')[1].decode(), 'bonjour — privé')
        text = subprocess.check_output([sys.executable, str(ROOT/'src/mxlink-cli.py'), 'get-text'], env=self.env)
        self.assertEqual(text.decode(), 'bonjour — privé')
        file = self.home / 'export file.txt'; file.write_bytes(b'contents')
        subprocess.check_call([sys.executable,str(ROOT/'src/mxlink-cli.py'),'send-files',str(file)],env=self.env)
        manifest=json.loads(self.request('GET','/clipboard/manifest?key=test-secret-only')[1])
        self.assertEqual(manifest['count'],1)
        path='/clipboard/item?key=test-secret-only&session='+manifest['session']+'&index=0'
        self.assertEqual(self.request('GET',path)[1],b'contents')
        self.assertNotIn('bonjour — privé', (self.home/'.local/state/mxlink/mxlink.log').read_text())

    def test_upload_signature_name_collision_and_privacy(self):
        for signature, ext in ((b'\x89PNG\r\n\x1a\n','png'),(b'\xff\xd8\xff','jpg'),(b'%PDF-','pdf'),(b'PK\x03\x04','zip')):
            status, _, _ = self.request('POST', '/upload?key=test-secret-only', signature+b'test',
                {'X-MX-Filename':'../sample-'+ext, 'Content-Type':'application/octet-stream'})
            self.assertEqual(status,200)
            file=self.home/'received'/('sample-'+ext+'.'+ext)
            self.assertEqual(file.read_bytes(),signature+b'test')
            self.assertEqual(file.stat().st_mode & 0o777,0o600)
        self.request('POST','/upload?key=test-secret-only&name=sample-png.png',b'new')
        self.assertEqual((self.home/'received/sample-png (2).png').read_bytes(),b'new')

    def test_invalid_lengths_and_json(self):
        for value, status in (('-1',400),('abc',400),('9999999999',413)):
            self.assertEqual(self.request('POST','/?key=test-secret-only',b'',{'Content-Length':value})[0],status)
        self.assertEqual(self.request('POST','/?key=test-secret-only',b'[]')[0],400)
        self.assertEqual(self.request('POST','/?key=test-secret-only',b'{')[0],400)
        self.assertEqual(self.request('POST','/?key=test-secret-only',b'',{'Transfer-Encoding':'chunked'})[0],400)

    def test_interrupted_upload_is_removed(self):
        sock=socket.create_connection(('127.0.0.1',8767))
        sock.sendall(b'POST /upload?key=test-secret-only&name=incomplete HTTP/1.1\r\nHost: localhost\r\nContent-Length: 200\r\n\r\nshort')
        sock.shutdown(socket.SHUT_WR)
        sock.recv(4096);sock.close()
        time.sleep(.1)
        self.assertFalse((self.home/'received/incomplete').exists())
        self.assertEqual(list((self.home/'received').glob('.mxlink-*')),[])

if __name__=='__main__':
    unittest.main()
