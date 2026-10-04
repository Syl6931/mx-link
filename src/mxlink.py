#!/usr/bin/env python3

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs, unquote, quote
from pathlib import Path
import datetime
import json
import logging
import mimetypes
import os
import re
import shutil
import secrets
import time
import subprocess
import threading
import sys

HOST = "127.0.0.1"
PORT = 8765

LOG_FILE = os.path.expanduser("~/.local/state/mxlink/mxlink.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [MX Link] %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
    ],
)



CONFIG_DIR = Path.home() / ".config" / "mxlink"
CONFIG_FILE = CONFIG_DIR / "config.json"

DEFAULT_CONFIG = {
    "receive_dir": "",
    "open_images": True,
    "image_opener": "default",
    "open_pdfs": True,
    "pdf_opener": "default",
    "notifications": True,
}

_config_lock = threading.Lock()


def load_config():
    cfg = DEFAULT_CONFIG.copy()

    try:
        data = json.loads(
            CONFIG_FILE.read_text(encoding="utf-8")
        )

        if isinstance(data, dict):
            for key in DEFAULT_CONFIG:
                if key in data:
                    cfg[key] = data[key]

    except FileNotFoundError:
        pass
    except Exception as exc:
        logging.warning(
            "Configuration illisible, valeurs par défaut utilisées : %s",
            exc
        )

    # Normalisation
    if not isinstance(cfg["receive_dir"], str):
        cfg["receive_dir"] = ""

    for key in ("open_images", "open_pdfs", "notifications"):
        if not isinstance(cfg[key], bool):
            cfg[key] = DEFAULT_CONFIG[key]

    for key in ("image_opener", "pdf_opener"):
        if not isinstance(cfg[key], str) or not cfg[key].strip():
            cfg[key] = "default"
        else:
            cfg[key] = cfg[key].strip()

    return cfg


def save_config(updates):
    with _config_lock:
        cfg = load_config()

        if "receive_dir" in updates:
            value = updates["receive_dir"]
            if not isinstance(value, str):
                raise ValueError("receive_dir doit être une chaîne")
            cfg["receive_dir"] = value.strip()

        for key in ("open_images", "open_pdfs", "notifications"):
            if key in updates:
                if not isinstance(updates[key], bool):
                    raise ValueError(f"{key} doit être un booléen")
                cfg[key] = updates[key]

        for key in ("image_opener", "pdf_opener"):
            if key in updates:
                value = updates[key]
                if not isinstance(value, str):
                    raise ValueError(f"{key} doit être une chaîne")
                cfg[key] = value.strip() or "default"

        CONFIG_DIR.mkdir(parents=True, exist_ok=True)

        tmp = CONFIG_FILE.with_suffix(".json.tmp")
        tmp.write_text(
            json.dumps(
                cfg,
                ensure_ascii=False,
                indent=2
            ) + "\n",
            encoding="utf-8"
        )

        os.replace(tmp, CONFIG_FILE)

    return cfg


def config_value(key, default=None):
    return load_config().get(key, default)


APPLICATION_DIRS = (
    Path.home() / ".local/share/applications",
    Path("/usr/local/share/applications"),
    Path("/usr/share/applications"),
)


def _read_desktop_entry(path):
    data = {}
    in_desktop_entry = False

    try:
        for raw_line in path.read_text(
            encoding="utf-8",
            errors="replace",
        ).splitlines():
            line = raw_line.strip()

            if not line or line.startswith("#"):
                continue

            if line.startswith("[") and line.endswith("]"):
                in_desktop_entry = line == "[Desktop Entry]"
                continue

            if not in_desktop_entry or "=" not in line:
                continue

            key, value = line.split("=", 1)
            data[key.strip()] = value.strip()

    except Exception:
        return {}

    return data


def _desktop_files():
    seen = set()

    for directory in APPLICATION_DIRS:
        if not directory.is_dir():
            continue

        try:
            items = sorted(directory.glob("*.desktop"))
        except Exception:
            continue

        for path in items:
            desktop_id = path.name

            if desktop_id in seen:
                continue

            seen.add(desktop_id)
            yield desktop_id, path


def _desktop_path(desktop_id):
    desktop_id = os.path.basename(desktop_id)

    for directory in APPLICATION_DIRS:
        candidate = directory / desktop_id

        if candidate.is_file():
            return candidate

    return None


def _desktop_label(desktop_id):
    path = _desktop_path(desktop_id)

    if path is None:
        return desktop_id.removesuffix(".desktop")

    data = _read_desktop_entry(path)

    return (
        data.get("Name[fr]")
        or data.get("Name")
        or desktop_id.removesuffix(".desktop")
    )


def _default_desktop_id(mime):
    exe = shutil.which("xdg-mime")

    if not exe:
        return ""

    try:
        result = subprocess.run(
            [exe, "query", "default", mime],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=2,
            check=False,
        )
    except Exception:
        return ""

    return result.stdout.strip()


def available_openers(kind, current="default"):
    if kind == "image":
        mimes = {"image/jpeg", "image/png"}
        default_mime = "image/jpeg"
    elif kind == "pdf":
        mimes = {"application/pdf"}
        default_mime = "application/pdf"
    else:
        return []

    default_id = _default_desktop_id(default_mime)
    default_label = _desktop_label(default_id) if default_id else ""

    result = [{
        "value": "default",
        "label": (
            f"Par défaut — {default_label}"
            if default_label
            else "Par défaut"
        ),
    }]

    if shutil.which("gio"):
        found = []

        for desktop_id, path in _desktop_files():
            data = _read_desktop_entry(path)

            if data.get("Type", "Application") != "Application":
                continue

            if data.get("Hidden", "").lower() == "true":
                continue

            mime_values = {
                value
                for value in data.get("MimeType", "").split(";")
                if value
            }

            if not (mime_values & mimes):
                continue

            label = (
                data.get("Name[fr]")
                or data.get("Name")
                or desktop_id.removesuffix(".desktop")
            )

            found.append((
                label.casefold(),
                desktop_id,
                {
                    "value": f"desktop:{desktop_id}",
                    "label": label,
                },
            ))

        seen_values = {"default"}

        for _sort_label, _desktop_id, item in sorted(found):
            if item["value"] in seen_values:
                continue

            result.append(item)
            seen_values.add(item["value"])

    if (
        isinstance(current, str)
        and current
        and current != "default"
        and current not in {item["value"] for item in result}
    ):
        result.append({
            "value": current,
            "label": f"Configurée — {current}",
        })

    return result





STATE_FILE = Path(
    os.path.expanduser("~/.local/state/mxlink/state.json")
)

STATE_FILE.parent.mkdir(
    parents=True,
    exist_ok=True
)

_state_lock = threading.Lock()

_batch_last_at = None
_batch_type = None
_batch_count = 0
_batch_bytes = 0

BATCH_WINDOW_SECONDS = 2.5


def default_state():
    return {
        "status": "ready",
        "last_type": None,
        "last_name": None,
        "last_time": None,
        "last_size": 0,
        "batch_type": None,
        "batch_count": 0,
        "batch_bytes": 0,
    }


def read_state():
    result = default_state()

    try:
        data = json.loads(
            STATE_FILE.read_text(
                encoding="utf-8"
            )
        )

        if isinstance(data, dict):
            result.update(data)

    except FileNotFoundError:
        pass
    except Exception as exc:
        logging.warning(
            "État MX Link illisible : %s",
            exc
        )

    # Le fait que cette API réponde signifie
    # que le daemon est prêt.
    result["status"] = "ready"

    return result


def write_state(state):
    tmp = STATE_FILE.with_suffix(".json.tmp")

    tmp.write_text(
        json.dumps(
            state,
            ensure_ascii=False,
            indent=2
        ) + "\n",
        encoding="utf-8"
    )

    os.replace(tmp, STATE_FILE)


def classify_mime(mime):
    mime = (
        mime
        .lower()
        .split(";", 1)[0]
        .strip()
    )

    if mime.startswith("image/"):
        return "image"

    if mime == "application/pdf":
        return "pdf"

    return "file"


def record_file_event(path, mime, size):
    global _batch_last_at
    global _batch_type
    global _batch_count
    global _batch_bytes

    now = datetime.datetime.now()
    event_type = classify_mime(mime)

    with _state_lock:

        same_batch = (
            _batch_last_at is not None
            and _batch_type == event_type
            and (
                now - _batch_last_at
            ).total_seconds()
            <= BATCH_WINDOW_SECONDS
        )

        if same_batch:
            _batch_count += 1
            _batch_bytes += size
        else:
            _batch_type = event_type
            _batch_count = 1
            _batch_bytes = size

        _batch_last_at = now

        state = {
            "status": "ready",

            "last_type": event_type,
            "last_name": Path(path).name,
            "last_time": now.strftime(
                "%H:%M:%S"
            ),
            "last_size": size,

            "batch_type": event_type,
            "batch_count": _batch_count,
            "batch_bytes": _batch_bytes,
        }

        state["last_direction"] = "in"
    write_state(state)


def record_simple_event(
    event_type,
    name,
    size=0
):
    global _batch_last_at
    global _batch_type
    global _batch_count
    global _batch_bytes

    now = datetime.datetime.now()

    with _state_lock:

        # Une URL ou un texte termine tout lot
        # de fichiers précédent.
        _batch_last_at = None
        _batch_type = None
        _batch_count = 0
        _batch_bytes = 0

        state = {
            "status": "ready",

            "last_type": event_type,
            "last_name": name,
            "last_time": now.strftime(
                "%H:%M:%S"
            ),
            "last_size": size,

            "batch_type": event_type,
            "batch_count": 1,
            "batch_bytes": size,
        }

        state["last_direction"] = "in"
    write_state(state)



def read_clipboard_live():
    commands = []

    qdbus = (
        shutil.which("qdbus6")
        or shutil.which("qdbus")
    )

    if qdbus:
        commands.append((
            [
                qdbus,
                "org.kde.klipper",
                "/klipper",
                "getClipboardContents",
            ],
            True
        ))

    wl_paste = shutil.which("wl-paste")

    if wl_paste:
        commands.append((
            [
                wl_paste,
                "--no-newline",
            ],
            False
        ))

    xclip = shutil.which("xclip")

    if xclip:
        commands.append((
            [
                xclip,
                "-selection",
                "clipboard",
                "-o",
            ],
            False
        ))

    for command, qdbus_output in commands:
        try:
            result = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
                timeout=2,
            )

            if result.returncode != 0:
                continue

            text = result.stdout

            # qdbus ajoute son propre retour ligne
            if qdbus_output and text.endswith("\n"):
                text = text[:-1]

            if text:
                return text

        except Exception:
            pass

    return None



def clipboard_file_paths():
    text = read_clipboard_live()

    if not text:
        return []

    tokens = text.split()

    if not tokens:
        return []

    if not all(
        token.startswith("file://")
        for token in tokens
    ):
        return []

    paths = []

    for token in tokens:
        try:
            parsed = urlparse(token)

            if parsed.scheme != "file":
                return []

            path = Path(
                unquote(parsed.path)
            )

            if not path.is_file():
                return []

            paths.append(path)

        except Exception:
            return []

    return paths


def clipboard_export_type():
    paths = clipboard_file_paths()

    if len(paths) == 1:
        return "file"

    if len(paths) > 1:
        return "files"

    text = read_clipboard_live()

    if not text:
        return "empty"

    if text.strip().startswith(
        ("http://", "https://")
    ):
        return "url"

    return "text"


_clipboard_sessions = {}
_clipboard_sessions_lock = threading.Lock()
CLIPBOARD_SESSION_TTL = 900


def cleanup_clipboard_sessions():
    now = time.time()

    with _clipboard_sessions_lock:
        expired = [
            key
            for key, value in _clipboard_sessions.items()
            if now - value["created"] > CLIPBOARD_SESSION_TTL
        ]

        for key in expired:
            _clipboard_sessions.pop(key, None)


def create_clipboard_session():
    cleanup_clipboard_sessions()

    paths = clipboard_file_paths()

    if not paths:
        return None

    session_id = secrets.token_urlsafe(18)

    snapshot = []

    for path in paths:
        stat = path.stat()

        snapshot.append({
            "path": str(path),
            "name": path.name,
            "size": stat.st_size,
            "mime": (
                mimetypes.guess_type(path.name)[0]
                or "application/octet-stream"
            ),
        })

    with _clipboard_sessions_lock:
        _clipboard_sessions[session_id] = {
            "created": time.time(),
            "items": snapshot,
        }

    return session_id, snapshot


def get_clipboard_session_item(session_id, index):
    cleanup_clipboard_sessions()

    with _clipboard_sessions_lock:
        session = _clipboard_sessions.get(session_id)

        if session is None:
            return None

        items = session["items"]

        if index < 0 or index >= len(items):
            return None

        return dict(items[index])



def record_outbound_activity(
    event_type,
    name,
    size=0,
    count=1
,
    names=None
):
    # Réutilise la mécanique existante pour date/type/nom/taille.
    record_simple_event(
        event_type,
        name,
        size
    )

    state = read_state()

    state["last_direction"] = "out"
    state["batch_type"] = event_type
    state["batch_count"] = count
    state["batch_bytes"] = size
    state["batch_names"] = (
        list(names)
        if names
        else [name]
    )

    write_state(state)

    logging.info(
        "Envoyé vers iPhone : %s (%d octets, %d élément(s))",
        name,
        size,
        count
    )


def mark_clipboard_session_item_delivered(
    session_id,
    index
):
    completed = None

    with _clipboard_sessions_lock:
        session = _clipboard_sessions.get(
            session_id
        )

        if session is None:
            return

        items = session["items"]

        delivered = session.setdefault(
            "delivered",
            set()
        )

        delivered.add(index)

        # On n'enregistre qu'une seule activité quand
        # TOUS les fichiers du snapshot ont bien été servis.
        if (
            len(delivered) == len(items)
            and not session.get("activity_recorded")
        ):
            session["activity_recorded"] = True

            count = len(items)
            total = sum(
                item["size"]
                for item in items
            )

            if count == 1:
                name = items[0]["name"]
            else:
                name = (
                    items[0]["name"]
                    + f" + {count - 1}"
                )

            completed = (
                "file",
                name,
                total,
                count,
                [
                    item["name"]
                    for item in items
                ]
            )

    if completed is not None:
        record_outbound_activity(
            *completed
        )


def notify(message):
    if not config_value("notifications", True):
        return

    exe = shutil.which("notify-send")
    if exe:
        subprocess.Popen(
            [exe, "MX Link", message],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )



# Regroupe les images reçues à quelques instants d'intervalle :
# un lot de photos ne déclenche qu'une seule demande d'ouverture.
_image_open_lock = threading.Lock()
_image_open_timer = None
_image_first_path = None
IMAGE_OPEN_DELAY = 1.2


def _open_pending_image():
    global _image_open_timer, _image_first_path

    with _image_open_lock:
        path = _image_first_path
        _image_first_path = None
        _image_open_timer = None

    if not path:
        return

    opener = config_value("image_opener", "default")

    if open_local_file(path, opener):
        logging.info(
            "Demande d'ouverture image envoyée via %s : %s",
            opener,
            path
        )
    else:
        logging.warning(
            "Impossible de demander l'ouverture automatique via %s : %s",
            opener,
            path
        )


def schedule_image_open(path):
    global _image_open_timer, _image_first_path

    with _image_open_lock:
        # On mémorise la première image du lot.
        if _image_first_path is None:
            _image_first_path = path

        # Chaque nouvelle image repousse légèrement l'ouverture.
        if _image_open_timer is not None:
            _image_open_timer.cancel()

        _image_open_timer = threading.Timer(
            IMAGE_OPEN_DELAY,
            _open_pending_image
        )
        _image_open_timer.daemon = True
        _image_open_timer.start()


def open_local_file(path, opener="default"):
    opener = (opener or "default").strip()

    if opener.startswith("desktop:"):
        desktop_id = opener.split(":", 1)[1]
        desktop_path = _desktop_path(desktop_id)
        gio = shutil.which("gio")

        if desktop_path is not None and gio:
            try:
                subprocess.Popen(
                    [gio, "launch", str(desktop_path), str(path)],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True,
                )
                return True
            except Exception as exc:
                logging.warning(
                    "Application configurée indisponible (%s), "
                    "retour à l'application système : %s",
                    opener,
                    exc,
                )
        else:
            logging.warning(
                "Application configurée indisponible (%s), "
                "retour à l'application système",
                opener,
            )

        opener = "default"

    if opener == "default":
        exe = shutil.which("xdg-open")
    elif os.path.isabs(opener):
        exe = (
            opener
            if os.path.isfile(opener)
            and os.access(opener, os.X_OK)
            else None
        )
    else:
        exe = shutil.which(opener)

    if not exe:
        exe = shutil.which("xdg-open")

        if not exe:
            return False

    try:
        subprocess.Popen(
            [exe, str(path)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        return True
    except Exception:
        return False


def download_dir():
    configured = config_value("receive_dir", "").strip()

    if configured:
        return Path(
            os.path.expandvars(
                os.path.expanduser(configured)
            )
        )

    try:
        path = subprocess.check_output(
            ["xdg-user-dir", "DOWNLOAD"],
            text=True
        ).strip()
        if path:
            return Path(path) / "MX Link"
    except Exception:
        pass

    return Path.home() / "Downloads" / "MX Link"


def safe_filename(name):
    name = unquote(name or "").strip()
    name = Path(name).name
    name = re.sub(r'[\x00-\x1f/\\:*?"<>|]', "_", name)
    return name[:180]


def unique_path(directory, filename):
    path = directory / filename

    if not path.exists():
        return path

    stem = path.stem
    suffix = path.suffix

    n = 2
    while True:
        candidate = directory / f"{stem} ({n}){suffix}"
        if not candidate.exists():
            return candidate
        n += 1


def sniff_type(raw, content_type):
    mime = content_type.split(";", 1)[0].strip().lower()

    # Si iOS nous fournit déjà quelque chose de précis, on le conserve.
    if mime not in ("", "application/octet-stream"):
        return mime

    # Détection par signature du fichier.
    if raw.startswith(b"%PDF-"):
        return "application/pdf"

    if raw.startswith(b"\\xff\\xd8\\xff"):
        return "image/jpeg"

    if raw.startswith(b"\\x89PNG\\r\\n\\x1a\\n"):
        return "image/png"

    if raw.startswith((b"GIF87a", b"GIF89a")):
        return "image/gif"

    if raw.startswith(b"PK\\x03\\x04"):
        return "application/zip"

    # HEIC / HEIF : boîte ISO BMFF contenant ftyp
    if len(raw) >= 12 and raw[4:8] == b"ftyp":
        brand = raw[8:12]
        if brand in (
            b"heic", b"heix", b"hevc", b"hevx",
            b"heim", b"heis", b"mif1", b"msf1",
        ):
            return "image/heic"

    return mime or "application/octet-stream"


def generated_filename(content_type):
    mime = content_type.split(";", 1)[0].strip().lower()

    aliases = {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/gif": ".gif",
        "image/heic": ".heic",
        "image/heif": ".heif",
        "application/pdf": ".pdf",
        "application/zip": ".zip",
        "application/octet-stream": ".bin",
    }

    ext = aliases.get(mime, mimetypes.guess_extension(mime) or ".bin")

    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    return f"iPhone-{stamp}{ext}"


def save_upload(raw, content_type, requested_name=None):
    directory = download_dir()
    directory.mkdir(parents=True, exist_ok=True)

    filename = safe_filename(requested_name)

    if not filename:
        filename = generated_filename(content_type)

    # Si iOS fournit un nom sans extension, on complète grâce au MIME.
    elif not Path(filename).suffix:
        generated = generated_filename(content_type)
        suffix = Path(generated).suffix

        if suffix and suffix != ".bin":
            filename += suffix

    path = unique_path(directory, filename)
    path.write_bytes(raw)

    return path


def copy_to_clipboard(text):
    qdbus = shutil.which("qdbus6") or shutil.which("qdbus")

    if qdbus:
        try:
            r = subprocess.run(
                [
                    qdbus,
                    "org.kde.klipper",
                    "/klipper",
                    "setClipboardContents",
                    text,
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=3,
            )
            if r.returncode == 0:
                return "klipper"
        except Exception:
            pass

    wl_copy = shutil.which("wl-copy")

    if wl_copy:
        try:
            r = subprocess.run(
                [wl_copy],
                input=text,
                text=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=3,
            )
            if r.returncode == 0:
                return "wl-copy"
        except Exception:
            pass

    return None


def open_url(url):
    browsers = [
        "google-chrome",
        "google-chrome-stable",
        "chromium",
        "chromium-browser",
        "xdg-open",
    ]

    for browser in browsers:
        path = shutil.which(browser)

        if not path:
            continue

        if browser in (
            "google-chrome",
            "google-chrome-stable",
            "chromium",
            "chromium-browser",
        ):
            helper = os.path.expanduser(
                "~/.local/share/mxlink/arm-maximize-chrome.sh"
            )

            if os.path.exists(helper):
                try:
                    subprocess.run(
                        [helper],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        timeout=2,
                    )
                except Exception:
                    pass

            command = [path, "--new-window", url]
        else:
            command = [path, url]

        subprocess.Popen(
            command,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )

        return browser

    return None


class Handler(BaseHTTPRequestHandler):

    def send_text(self, status, text):
        body = text.encode("utf-8")

        self.send_response(status)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()

        self.wfile.write(body)

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)

        if path == "/clipboard/manifest":
            result = create_clipboard_session()

            if result is None:
                payload = {
                    "available": False,
                    "session": None,
                    "count": 0,
                    "total_bytes": 0,
                    "items": [],
                }
            else:
                session_id, items = result

                payload = {
                    "available": True,
                    "session": session_id,
                    "count": len(items),
                    "total_bytes": sum(
                        item["size"]
                        for item in items
                    ),
                    "items": [
                        {
                            "index": index,
                            "name": item["name"],
                            "size": item["size"],
                            "mime": item["mime"],
                        }
                        for index, item in enumerate(items)
                    ],
                }

            body = json.dumps(
                payload,
                ensure_ascii=False
            ).encode("utf-8")

            self.send_response(200)
            self.send_header(
                "Content-Type",
                "application/json; charset=utf-8"
            )
            self.send_header(
                "Content-Length",
                str(len(body))
            )
            self.end_headers()
            self.wfile.write(body)
            return

        if path == "/clipboard/item":
            try:
                session_id = query["session"][0]
                index = int(query["index"][0])
            except (
                KeyError,
                IndexError,
                TypeError,
                ValueError,
            ):
                self.send_text(
                    400,
                    "Paramètres session/index invalides"
                )
                return

            item = get_clipboard_session_item(
                session_id,
                index
            )

            if item is None:
                self.send_text(
                    404,
                    "Session ou fichier introuvable"
                )
                return

            file_path = Path(item["path"])

            if not file_path.is_file():
                self.send_text(
                    404,
                    "Le fichier n'existe plus"
                )
                return

            size = file_path.stat().st_size

            self.send_response(200)
            self.send_header(
                "Content-Type",
                item["mime"]
            )
            self.send_header(
                "Content-Length",
                str(size)
            )
            self.send_header(
                "Content-Disposition",
                "attachment; filename*=UTF-8''"
                + quote(item["name"])
            )
            self.end_headers()

            with file_path.open("rb") as source:
                shutil.copyfileobj(
                    source,
                    self.wfile,
                    length=1024 * 1024
                )

            mark_clipboard_session_item_delivered(
                session_id,
                index
            )

            return

        if self.path == "/clipboard/type":
            body = clipboard_export_type().encode(
                "utf-8"
            )

            self.send_response(200)
            self.send_header(
                "Content-Type",
                "text/plain; charset=utf-8"
            )
            self.send_header(
                "Content-Length",
                str(len(body))
            )
            self.end_headers()
            self.wfile.write(body)
            return

        if self.path == "/clipboard/raw":
            text = read_clipboard_live() or ""
            body = text.encode("utf-8")

            self.send_response(200)
            self.send_header(
                "Content-Type",
                "text/plain; charset=utf-8"
            )
            self.send_header(
                "Content-Length",
                str(len(body))
            )
            self.end_headers()
            self.wfile.write(body)

            if text:
                stripped = text.strip()

                event_type = (
                    "url"
                    if stripped.startswith(
                        ("http://", "https://")
                    )
                    else "text"
                )

                record_outbound_activity(
                    event_type,
                    "Presse-papiers",
                    len(body),
                    1
                )

            return

        if self.path == "/clipboard":
            text = read_clipboard_live()

            if text:
                stripped = text.strip()

                item_type = (
                    "url"
                    if stripped.startswith(
                        ("http://", "https://")
                    )
                    else "text"
                )

                result = {
                    "available": True,
                    "type": item_type,
                    "content": text,
                    "size": len(
                        text.encode("utf-8")
                    ),
                }

            else:
                result = {
                    "available": False,
                    "type": None,
                    "content": "",
                    "size": 0,
                }

            body = json.dumps(
                result,
                ensure_ascii=False
            ).encode("utf-8")

            self.send_response(200)
            self.send_header(
                "Content-Type",
                "application/json; charset=utf-8"
            )
            self.send_header(
                "Content-Length",
                str(len(body))
            )
            self.end_headers()
            self.wfile.write(body)
            return

        if self.path == "/state":
            body = json.dumps(
                read_state(),
                ensure_ascii=False
            ).encode("utf-8")

            self.send_response(200)
            self.send_header(
                "Content-Type",
                "application/json; charset=utf-8"
            )
            self.send_header(
                "Content-Length",
                str(len(body))
            )
            self.end_headers()
            self.wfile.write(body)
            return

        if self.path == "/open-folder":
            path = download_dir()

            try:
                path.mkdir(
                    parents=True,
                    exist_ok=True
                )

                if open_local_file(path):
                    self.send_text(
                        200,
                        "Dossier ouvert"
                    )
                else:
                    self.send_text(
                        500,
                        "Impossible d'ouvrir le dossier"
                    )

            except Exception as exc:
                logging.exception(
                    "Erreur ouverture dossier : %s",
                    exc
                )

                self.send_text(
                    500,
                    "Erreur ouverture dossier"
                )

            return

        if self.path == "/openers":
            cfg = load_config()

            body = json.dumps(
                {
                    "images": available_openers(
                        "image",
                        cfg.get("image_opener", "default"),
                    ),
                    "pdfs": available_openers(
                        "pdf",
                        cfg.get("pdf_opener", "default"),
                    ),
                },
                ensure_ascii=False,
            ).encode("utf-8")

            self.send_response(200)
            self.send_header(
                "Content-Type",
                "application/json; charset=utf-8",
            )
            self.send_header(
                "Content-Length",
                str(len(body)),
            )
            self.end_headers()
            self.wfile.write(body)
            return

        if self.path == "/config":
            cfg = load_config()
            cfg["receive_dir_resolved"] = str(download_dir())

            body = json.dumps(
                cfg,
                ensure_ascii=False
            ).encode("utf-8")

            self.send_response(200)
            self.send_header(
                "Content-Type",
                "application/json; charset=utf-8"
            )
            self.send_header(
                "Content-Length",
                str(len(body))
            )
            self.end_headers()
            self.wfile.write(body)
            return

        if self.path == "/status":

            log_path = (
                Path.home()
                / ".local/state/mxlink/mxlink.log"
            )

            result = {
                "status": "ready",
                "last_type": None,
                "last_name": None,
                "last_time": None
            }

            try:
                lines = log_path.read_text(
                    errors="replace"
                ).splitlines()

                for line in reversed(lines):

                    m = re.search(
                        r'^(\d\d:\d\d:\d\d).*Fichier enregistré : (.+?) '
                        r'\(\d+ octets, ([^)]+)\)',
                        line
                    )

                    if m:
                        result["last_time"] = m.group(1)
                        result["last_name"] = Path(m.group(2)).name

                        mime = m.group(3)

                        if mime.startswith("image/"):
                            result["last_type"] = "image"
                        elif mime == "application/pdf":
                            result["last_type"] = "pdf"
                        else:
                            result["last_type"] = "file"

                        break

                    m = re.search(
                        r'^(\d\d:\d\d:\d\d).*URL ouverte : (.+)$',
                        line
                    )

                    if m:
                        result["last_time"] = m.group(1)
                        result["last_name"] = m.group(2)
                        result["last_type"] = "url"
                        break

                    m = re.search(
                        r'^(\d\d:\d\d:\d\d).*Texte',
                        line
                    )

                    if m:
                        result["last_time"] = m.group(1)
                        result["last_name"] = "Texte copié"
                        result["last_type"] = "text"
                        break

            except Exception as e:
                result["status"] = "ready"
                result["error"] = str(e)

            body = json.dumps(
                result,
                ensure_ascii=False
            ).encode("utf-8")

            self.send_response(200)
            self.send_header(
                "Content-Type",
                "application/json; charset=utf-8"
            )
            self.send_header(
                "Content-Length",
                str(len(body))
            )
            self.end_headers()
            self.wfile.write(body)
            return

        if self.path == "/mxlink-ca.cer":
            ca = (
                Path.home()
                / ".local/share/mxlink/tls/mxlink-ca.crt"
            )

            if not ca.exists():
                self.send_text(404, "CA introuvable")
                return

            body = ca.read_bytes()

            self.send_response(200)
            self.send_header(
                "Content-Type",
                "application/x-x509-ca-cert"
            )
            self.send_header(
                "Content-Disposition",
                'attachment; filename="MX-Link-CA.cer"'
            )
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        if self.path in ("/", "/health"):
            self.send_text(200, "MX Link OK")
        else:
            self.send_text(404, "Not found")

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))

        # Protection grossière contre un envoi aberrant
        if length > 1024 * 1024 * 500:
            self.send_text(413, "Fichier trop volumineux")
            return

        raw = self.rfile.read(length)
        source = self.client_address[0]

        parsed = urlparse(self.path)

        if parsed.path == "/config":
            try:
                updates = json.loads(
                    raw.decode("utf-8")
                )

                if not isinstance(updates, dict):
                    raise ValueError(
                        "Le corps doit être un objet JSON"
                    )

                cfg = save_config(updates)
                cfg["receive_dir_resolved"] = str(download_dir())

                body = json.dumps(
                    cfg,
                    ensure_ascii=False
                ).encode("utf-8")

                self.send_response(200)
                self.send_header(
                    "Content-Type",
                    "application/json; charset=utf-8"
                )
                self.send_header(
                    "Content-Length",
                    str(len(body))
                )
                self.end_headers()
                self.wfile.write(body)

                logging.info(
                    "Configuration mise à jour : %s",
                    cfg
                )

            except (ValueError, json.JSONDecodeError) as exc:
                self.send_text(
                    400,
                    f"Configuration invalide : {exc}"
                )

            return

        logging.info(
            "Reçu depuis %s : %s (%d octets)",
            source,
            parsed.path,
            length,
        )

        # ------------------------------------------------------------------
        # FICHIER / PHOTO
        # ------------------------------------------------------------------

        if parsed.path == "/upload":

            query = parse_qs(parsed.query)

            requested_name = self.headers.get("X-MX-Filename")

            # iOS Shortcuts peut parfois replier notre en-tête personnalisé
            # dans la valeur d'un autre en-tête HTTP.
            if not requested_name:
                for header_name, header_value in self.headers.items():
                    value = str(header_value)

                    match = re.search(
                        r"X-MX-Filename\\s*:\\s*([^\\r\\n]+)",
                        value,
                        re.IGNORECASE,
                    )

                    if match:
                        requested_name = match.group(1).strip()

                        logging.info(
                            "Nom récupéré dans %s : %r",
                            header_name,
                            requested_name,
                        )
                        break

            if not requested_name:
                requested_name = query.get("name", [None])[0]

            content_type = self.headers.get(
                "Content-Type",
                "application/octet-stream"
            )

            detected_type = sniff_type(raw, content_type)

            if detected_type != content_type:
                logging.info(
                    "Type détecté : %s → %s",
                    content_type,
                    detected_type,
                )

            content_type = detected_type

            try:
                path = save_upload(
                    raw,
                    content_type,
                    requested_name,
                )
            except Exception as exc:
                logging.exception("Erreur réception fichier : %s", exc)
                self.send_text(500, "Erreur lors de l'enregistrement")
                return

            logging.info(
                "Fichier enregistré : %s (%d octets, %s)",
                path,
                len(raw),
                content_type,
            )

            mime = content_type.lower().split(";", 1)[0].strip()
            is_image = mime.startswith("image/")
            is_pdf = mime == "application/pdf" or path.suffix.lower() == ".pdf"

            record_file_event(
                path,
                mime,
                len(raw)
            )

            if is_image:
                notify(f"Photo reçue : {path.name}")

                if config_value("open_images", True):
                    schedule_image_open(path)
                    logging.info("Photo ajoutée au lot : %s", path)
                else:
                    logging.info(
                        "Ouverture automatique image désactivée : %s",
                        path
                    )

            elif is_pdf:
                notify(f"PDF reçu : {path.name}")

                if config_value("open_pdfs", True):
                    opener = config_value("pdf_opener", "default")

                    if open_local_file(path, opener):
                        logging.info(
                            "Demande d'ouverture PDF envoyée via %s : %s",
                            opener,
                            path
                        )
                    else:
                        logging.warning(
                            "Impossible de demander l'ouverture PDF via %s : %s",
                            opener,
                            path
                        )
                else:
                    logging.info(
                        "Ouverture automatique PDF désactivée : %s",
                        path
                    )

            else:
                notify(f"Fichier reçu : {path.name}")

            self.send_text(200, f"Reçu : {path.name}")
            return

        # ------------------------------------------------------------------
        # JSON : URL / TEXTE
        # ------------------------------------------------------------------

        try:
            data = json.loads(raw.decode("utf-8"))
        except Exception as exc:
            logging.error("JSON invalide : %s", exc)
            self.send_text(400, "Invalid JSON")
            return

        url = data.get("url")

        if isinstance(url, str) and url.startswith(("http://", "https://")):

            browser = open_url(url)

            if browser:
                logging.info("URL ouverte : %s", url)

                record_simple_event(
                    "url",
                    url,
                    len(url.encode("utf-8"))
                )
                notify("URL reçue depuis l’iPhone")
                self.send_text(200, "URL ouverte sur MX")
            else:
                logging.error("Aucun navigateur trouvé")
                self.send_text(500, "Navigateur introuvable")

            return

        text = data.get("text")

        if isinstance(text, str):

            method = copy_to_clipboard(text)

            if method:
                logging.info(
                    "Texte copié via %s : %r",
                    method,
                    text[:100],
                )

                record_simple_event(
                    "text",
                    "Texte copié",
                    len(text.encode("utf-8"))
                )
                notify("Texte copié dans le presse-papiers")
                self.send_text(200, "Texte copié sur MX")
            else:
                logging.error("Presse-papiers indisponible")
                self.send_text(500, "Presse-papiers indisponible")

            return

        logging.warning("Message non reconnu : %s", data)
        self.send_text(400, "Message MX Link non reconnu")

    def log_message(self, format, *args):
        pass


if __name__ == "__main__":

    logging.info("Démarrage")
    logging.info("Écoute sur %s:%s", HOST, PORT)

    server = ThreadingHTTPServer((HOST, PORT), Handler)

    try:
        server.serve_forever()
    finally:
        server.server_close()
        logging.info("Arrêt")
