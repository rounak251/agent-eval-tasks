#!/bin/bash
# Oracle: key the cursor on (ts, id) so ties across a page boundary are not skipped.
set -euo pipefail
APP_DIR="${APP_DIR:-/app}"
cat > "$APP_DIR/feed/pagination.py" <<'PY'
"""Cursor pagination for the activity feed.

An event is a dict with at least an integer ``id`` (unique) and an integer
``ts`` (unix seconds). Pages are returned newest first.
"""
import base64
import json


def _encode(value):
    return base64.urlsafe_b64encode(json.dumps(value).encode()).decode()


def _decode(cursor):
    return json.loads(base64.urlsafe_b64decode(cursor.encode()))


def _key(e):
    return (e["ts"], e["id"])


def list_events(events, limit, cursor=None):
    """Return ``(page, next_cursor)``.

    ``next_cursor`` is an opaque string to pass back for the next page, or
    ``None`` when there is nothing more to fetch.
    """
    if limit < 1:
        raise ValueError("limit must be positive")
    rows = sorted(events, key=_key, reverse=True)
    if cursor is not None:
        last = tuple(_decode(cursor))
        rows = [e for e in rows if _key(e) < last]
    page = rows[:limit]
    next_cursor = _encode(list(_key(page[-1]))) if len(rows) > limit else None
    return page, next_cursor
PY
