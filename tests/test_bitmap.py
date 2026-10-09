"""MX Link bitmap clipboard regression tests; never touch the real clipboard."""
import importlib.util
import os
import pathlib
import shutil
import struct
import subprocess
import sys
import tempfile
import time
import unittest
import zlib

SRC = pathlib.Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))
import mxlink_bitmap as bitmap


def test_png():
    def chunk(tag, payload):
        return (struct.pack(">I", len(payload)) + tag + payload +
                struct.pack(">I", zlib.crc32(tag + payload) & 0xffffffff))
    raw = b"\x00\xff\x00\x00\xff\x00\x00\xff\xff"
    return (bitmap.PNG_SIGNATURE +
            chunk(b"IHDR", struct.pack(">IIBBBBB", 2, 1, 8, 2, 0, 0, 0)) +
            chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))


class BitmapTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # mxlink.py sets a FileHandler at import time: use private test HOME.
        cls.sandbox = tempfile.TemporaryDirectory(prefix="mxlink-unit-")
        cls.home = pathlib.Path(cls.sandbox.name)
        (cls.home / ".local/state/mxlink").mkdir(parents=True)
        cls.prev_home = os.environ.get("HOME")
        os.environ["HOME"] = str(cls.home)
        spec = importlib.util.spec_from_file_location("mxlink_test_app", SRC / "mxlink.py")
        cls.app = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.app)
        cls.cache = bitmap.CACHE
        bitmap.CACHE = cls.home / "bitmaps"

    @classmethod
    def tearDownClass(cls):
        bitmap.CACHE = cls.cache
        if cls.prev_home is None:
            os.environ.pop("HOME", None)
        else:
            os.environ["HOME"] = cls.prev_home
        cls.sandbox.cleanup()

    def setUp(self):
        self.real_which = bitmap.shutil.which
        self.old_file_paths = self.app.clipboard_file_paths
        self.old_image_mime = self.app.image_mime
        self.old_capture_image = self.app.capture_image
        self.old_read_clipboard = self.app.read_clipboard_live
        self.clipboard_contents = test_png()
        self.mime = "image/png"
        self.data_path = self.home / "clipboard-content.bin"
        self.data_path.write_bytes(self.clipboard_contents)
        self.fake_tool = self.home / "wl-paste"
        self.fake_tool.write_text(
            "#!/usr/bin/env python3\nimport sys\n"
            "if '--list-types' in sys.argv:\n"
            "  print('text/plain\\n' + " + repr(self.mime) + ")\n"
            "elif '--type' in sys.argv:\n"
            "  sys.stdout.buffer.write(open(" + repr(str(self.data_path)) + ", 'rb').read())\n"
            "else: sys.exit(3)\n")
        self.fake_tool.chmod(0o700)
        bitmap.shutil.which = lambda name: (str(self.fake_tool) if name == "wl-paste"
                                             else self.real_which(name))
        self.app.image_mime = bitmap.image_mime
        self.app.capture_image = bitmap.capture_image
        self.app.clipboard_file_paths = lambda: []
        self.app._clipboard_sessions.clear()

    def tearDown(self):
        bitmap.shutil.which = self.real_which
        self.app.clipboard_file_paths = self.old_file_paths
        self.app.image_mime = self.old_image_mime
        self.app.capture_image = self.old_capture_image
        self.app.read_clipboard_live = self.old_read_clipboard
        bitmap.clean_expired(
            [item for s in self.app._clipboard_sessions.values() for item in s["items"]]
        )
        self.app._clipboard_sessions.clear()

    def test_png_is_exposed_as_one_private_file(self):
        self.assertEqual(bitmap.image_mime(), "image/png")
        self.assertEqual(self.app.clipboard_export_type(), "file")
        sid, items = self.app.create_clipboard_session()
        self.assertTrue(sid)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["mime"], "image/png")
        self.assertEqual(items[0]["name"][-4:], ".png")
        target = pathlib.Path(items[0]["path"])
        self.assertEqual(target.read_bytes(), self.clipboard_contents)
        self.assertEqual(target.stat().st_mode & 0o777, 0o600)
        self.assertEqual(target.parent.stat().st_mode & 0o777, 0o700)
        self.app._clipboard_sessions[sid]["created"] = time.time() - 1000
        self.app.cleanup_clipboard_sessions()
        self.assertFalse(target.exists())

    def test_bmp_is_converted_to_png(self):
        if not self.real_which("magick"):
            self.skipTest("ImageMagick is not installed")
        subprocess.run(["magick", "-size", "2x2", "xc:blue", "BMP3:" + str(self.data_path)],
                       check=True)
        self.fake_tool.write_text(self.fake_tool.read_text().replace("image/png", "image/bmp"))
        captured = bitmap.capture_image("image/bmp")
        self.assertIsNotNone(captured)
        target = pathlib.Path(captured["path"])
        self.assertEqual(target.read_bytes()[:8], bitmap.PNG_SIGNATURE)
        self.assertEqual(target.stat().st_mode & 0o777, 0o600)
        bitmap.clean_expired([captured])
        self.assertFalse(target.exists())

    def test_files_retain_precedence(self):
        source = self.home / "example.txt"
        source.write_text("test", encoding="utf-8")
        self.app.clipboard_file_paths = lambda: [source]
        self.assertEqual(self.app.clipboard_export_type(), "file")
        _, items = self.app.create_clipboard_session()
        self.assertEqual(items[0]["name"], "example.txt")
        self.assertNotIn("temporary", items[0])
        bitmap.clean_expired(items)
        self.assertTrue(source.exists())

    def test_text_and_empty_clipboard(self):
        self.app.image_mime = lambda: None
        self.app.read_clipboard_live = lambda: "bonjour"
        self.assertEqual(self.app.clipboard_export_type(), "text")
        self.app.read_clipboard_live = lambda: None
        self.assertEqual(self.app.clipboard_export_type(), "empty")
        self.assertIsNone(self.app.create_clipboard_session())

    def test_does_not_delete_non_temporary_files(self):
        file = self.home / "user-file.png"
        file.write_bytes(test_png())
        bitmap.clean_expired([{"path": str(file), "temporary": False}])
        self.assertTrue(file.exists())


if __name__ == "__main__":
    unittest.main()
