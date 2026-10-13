"""History is local, bounded, and never keeps clipboard text payloads."""
from pathlib import Path
import os
import stat
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
import mxlink_history as history


class HistoryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='mxlink-history-')
        self.root = Path(self.tmp.name)
        self.original = history.HISTORY_FILE
        history.HISTORY_FILE = self.root / 'history.json'

    def tearDown(self):
        history.HISTORY_FILE = self.original
        self.tmp.cleanup()

    def test_file_open_and_missing(self):
        f = self.root / 'photo.png'
        f.write_bytes(b'test')
        event_id = history.record('in', 'image', f.name, 4, paths=[f])
        entry = history.history_public()[0]
        self.assertEqual(entry['id'], event_id)
        self.assertTrue(entry['items'][0]['available'])
        self.assertNotIn('path', entry['items'][0])
        self.assertEqual(history.resolve(event_id, 0), ('file', str(f)))
        f.unlink()
        self.assertFalse(history.history_public()[0]['items'][0]['available'])
        self.assertIsNone(history.resolve(event_id, 0))

    def test_batches_are_one_operation_with_individual_targets(self):
        files = [self.root / f'p{i}.png' for i in (1, 2, 3)]
        for f in files:
            f.write_bytes(b'png')
            history.record('in', 'image', f.name, 3, paths=[f], batch_id='one-batch')
        entries = history.history_public()
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]['size'], 9)
        self.assertEqual(len(entries[0]['items']), 3)
        self.assertEqual(history.resolve('one-batch', 1), ('file', str(files[1])))
        self.assertIsNone(history.resolve('one-batch', -1))
        self.assertIsNone(history.resolve('one-batch', True))
        self.assertIsNone(history.resolve('wrong', 0))

    def test_clipboard_text_is_not_retained(self):
        history.record('in', 'text', 'A very private sentence', 23)
        raw = history.HISTORY_FILE.read_text()
        self.assertNotIn('private', raw)
        self.assertEqual(history.history_public()[0]['items'][0]['name'], 'Texte copié')
        self.assertFalse(history.history_public()[0]['items'][0]['available'])

    def test_url_and_retention_and_clear(self):
        uid = history.record('out', 'url', 'link', url='https://example.org')
        self.assertEqual(history.resolve(uid, 0), ('url', 'https://example.org'))
        for i in range(35):
            history.record('in', 'text', 'sensitive', i)
        self.assertEqual(len(history.history_public()), 30)
        self.assertIsNone(history.resolve(uid, 0))
        self.assertEqual(stat.S_IMODE(history.HISTORY_FILE.stat().st_mode), 0o600)
        history.clear()
        self.assertFalse(history.HISTORY_FILE.exists())
        self.assertEqual(history.history_public(), [])


if __name__ == '__main__':
    unittest.main()
