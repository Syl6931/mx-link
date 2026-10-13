"""Private local transfer history. Does not retain clipboard text contents."""
import datetime
import json
import os
from pathlib import Path
import secrets
import threading

LIMIT = 30
LOCK = threading.RLock()
HISTORY_FILE = Path.home() / '.local/state/mxlink/history.json'


def _load():
    try:
        data = json.loads(HISTORY_FILE.read_text(encoding='utf-8'))
        return data if isinstance(data, list) else []
    except (OSError, ValueError):
        return []


def record(direction, kind, name, size=0, paths=None, url=None, batch_id=None):
    """Record a completed transfer. Reuse batch_id to group incoming files."""
    if kind == 'text':
        name = 'Texte copié' if direction == 'in' else 'Texte transféré'
        paths = None
        url = None
    if paths:
        items = [{'name': Path(p).name, 'path': str(p)} for p in paths]
    elif kind == 'url' and url and url.startswith(('https://', 'http://')):
        items = [{'name': url, 'url': url}]
    else:
        items = [{'name': name}]
    now = datetime.datetime.now().astimezone()
    with LOCK:
        history = _load()
        existing = next((x for x in history if x.get('id') == batch_id), None) if batch_id else None
        if existing is not None:
            existing['items'].extend(items)
            existing['size'] = existing.get('size', 0) + size
            existing['date'] = now.isoformat(timespec='seconds')
            history.remove(existing)
            history.insert(0, existing)
            event_id = existing['id']
        else:
            event_id = batch_id or secrets.token_urlsafe(12)
            history.insert(0, {
                'id': event_id, 'date': now.isoformat(timespec='seconds'),
                'direction': direction, 'type': kind, 'size': size,
                'items': items,
            })
        HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
        tmp = HISTORY_FILE.with_name(HISTORY_FILE.name + '.tmp')
        try:
            with tmp.open('w', encoding='utf-8') as fp:
                os.chmod(tmp, 0o600)
                json.dump(history[:LIMIT], fp, ensure_ascii=False, indent=2)
                fp.write('\n')
            os.replace(tmp, HISTORY_FILE)
        finally:
            tmp.unlink(missing_ok=True)
    return event_id


def history_public():
    """No local paths are exposed to the QML applet or network clients."""
    with LOCK:
        history = _load()
        return [{
            'id': evt['id'], 'date': evt['date'],
            'direction': evt['direction'], 'type': evt['type'],
            'size': evt.get('size', 0),
            'items': [{
                'name': item.get('name', ''),
                'available': (
                    Path(item['path']).is_file() if 'path' in item else
                    item.get('url', '').startswith(('http://', 'https://'))
                )
            } for item in evt.get('items', [])],
        } for evt in history]


def resolve(event_id, item_index):
    """Only return targets previously registered by a successful transfer."""
    with LOCK:
        for evt in _load():
            if evt.get('id') != event_id:
                continue
            items = evt.get('items', [])
            if not isinstance(item_index, int) or isinstance(item_index, bool) or not 0 <= item_index < len(items):
                return None
            item = items[item_index]
            if 'path' in item:
                p = Path(item['path'])
                return ('file', str(p)) if p.is_file() else None
            url = item.get('url')
            if isinstance(url, str) and url.startswith(('https://', 'http://')):
                return ('url', url)
            return None
    return None


def clear():
    with LOCK:
        HISTORY_FILE.unlink(missing_ok=True)
