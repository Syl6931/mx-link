"""Capture des pixels du presse-papiers Wayland pour MX Link (iPhone)."""
import datetime
import os
import secrets
import shutil
import subprocess
import time
from pathlib import Path

TYPES = ("image/png", "image/jpeg", "image/bmp", "image/webp", "image/tiff")
EXTENSIONS = {"image/png": ".png", "image/jpeg": ".jpg", "image/bmp": ".bmp",
              "image/webp": ".webp", "image/tiff": ".tiff"}
CACHE = Path.home() / ".cache" / "mxlink" / "clipboard-bitmaps"
MAX_BYTES = 80 * 1024 * 1024
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def image_mime():
    tool = shutil.which("wl-paste")
    if not tool:
        return None
    try:
        res = subprocess.run([tool, "--list-types"], capture_output=True,
                             text=True, timeout=3, check=False)
        if res.returncode:
            return None
        offered = {line.strip().split(";", 1)[0].lower()
                   for line in res.stdout.splitlines()}
        return next((mime for mime in TYPES if mime in offered), None)
    except (OSError, subprocess.SubprocessError):
        return None


def capture_image(mime=None):
    """Export en PNG 0600, sans modifier le presse-papiers d'origine."""
    mime = mime or image_mime()
    wl_paste = shutil.which("wl-paste")
    if mime not in TYPES or not wl_paste:
        return None
    CACHE.mkdir(mode=0o700, parents=True, exist_ok=True)
    ident = secrets.token_hex(12)
    source = CACHE / (ident + EXTENSIONS[mime])
    target = CACHE / (ident + ".png")
    success = False
    try:
        with source.open("xb") as out:
            os.chmod(source, 0o600)
            proc = subprocess.run([wl_paste, "--type", mime], stdout=out,
                                  stderr=subprocess.DEVNULL, timeout=12,
                                  check=False)
        if proc.returncode or not (8 < source.stat().st_size <= MAX_BYTES):
            return None
        if mime != "image/png":
            magick = shutil.which("magick")
            if not magick:
                return None
            proc = subprocess.run(
                [magick, "-limit", "memory", "256MiB", "-limit", "map", "256MiB",
                 "-limit", "disk", "512MiB", str(source), "-strip", "png:" + str(target)],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                timeout=20, check=False,
            )
            if proc.returncode:
                return None
        if target.is_file():
            os.chmod(target, 0o600)
        if not target.is_file() or not (8 < target.stat().st_size <= MAX_BYTES):
            return None
        with target.open("rb") as handle:
            if handle.read(8) != PNG_SIGNATURE:
                return None
        success = True
        return {
            "path": str(target),
            "name": "MX-Link-image-" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S") + ".png",
            "size": target.stat().st_size,
            "mime": "image/png",
            "temporary": True,
        }
    except (OSError, subprocess.SubprocessError):
        return None
    finally:
        if source != target:
            source.unlink(missing_ok=True)
        if not success:
            target.unlink(missing_ok=True)


def clean_expired(items, now=None):
    """Efface uniquement les PNG créés par MX Link et devenus inutiles."""
    for item in items:
        if item.get("temporary"):
            file = Path(item["path"])
            if file.parent == CACHE:
                file.unlink(missing_ok=True)
    if CACHE.is_dir():
        now = now or time.time()
        for path in CACHE.glob("*.png"):
            try:
                if now - path.stat().st_mtime > 3600:
                    path.unlink(missing_ok=True)
            except OSError:
                pass
