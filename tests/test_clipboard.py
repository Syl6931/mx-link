"""Backend selection tests; subprocesses and clipboard access are mocked."""
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from types import SimpleNamespace
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'src'))
import mxlink_clipboard as clipboard

class ClipboardTests(unittest.TestCase):
    def test_x11_write_uses_stdin(self):
        with patch.dict(os.environ, {'DISPLAY':':test'}, clear=True), patch.object(clipboard.shutil,'which',return_value='/fake/xclip'), patch.object(clipboard.subprocess,'run',return_value=SimpleNamespace(returncode=0)) as run:
            self.assertEqual(clipboard.write_text('secret'),'xclip')
            self.assertEqual(run.call_args.args[0],['xclip','-selection','clipboard'])
            self.assertEqual(run.call_args.kwargs['input'],b'secret')
    def test_wayland_read_requests_text(self):
        def fake(command, **kwargs):
            self.assertEqual(command,['wl-paste','--no-newline','--type','text'])
            kwargs['stdout'].write(b'value')
            return SimpleNamespace(returncode=0)
        with patch.dict(os.environ,{'WAYLAND_DISPLAY':'test'},clear=True),patch.object(clipboard.shutil,'which',return_value='/fake'),patch.object(clipboard.subprocess,'run',side_effect=fake):
            self.assertEqual(clipboard.read_text(),'value')
    def test_uri_with_spaces(self):
        with tempfile.TemporaryDirectory() as name:
            file=Path(name)/'two words.txt';file.write_text('test')
            with patch.object(clipboard,'graphical',return_value=True),patch.object(clipboard,'read_text',return_value=file.as_uri()),patch.dict(os.environ,{},clear=True):
                self.assertEqual(clipboard.file_paths(),[file])
    def test_forced_headless_and_private_state(self):
        with tempfile.TemporaryDirectory() as name,patch.dict(os.environ,{'MXLINK_HEADLESS':'1','DISPLAY':':test'},clear=True),patch.object(clipboard,'STATE',Path(name)/'exchange.json'):
            self.assertEqual(clipboard.write_text('value'),'headless')
            self.assertEqual(clipboard.read_text(),'value')
            self.assertEqual(clipboard.STATE.stat().st_mode & 0o777,0o600)
