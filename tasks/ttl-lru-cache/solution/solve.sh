#!/bin/bash
# Oracle: monotonic default clock, refresh recency on hit, purge expired before evicting.
set -euo pipefail
APP_DIR="${APP_DIR:-/app}"
cat > "$APP_DIR/cachelib/ttl.py" <<'PY'
"""A small LRU cache whose entries expire after a fixed time-to-live."""
import time
from collections import OrderedDict

_MISSING = object()


class TTLCache:
    def __init__(self, maxsize, ttl, clock=time.monotonic):
        if maxsize < 1 or ttl <= 0:
            raise ValueError("maxsize must be >= 1 and ttl > 0")
        self.maxsize = maxsize
        self.ttl = ttl
        self._clock = clock
        self._data = OrderedDict()  # key -> (value, expires_at), least recent first

    def _purge(self):
        now = self._clock()
        for key in [k for k, (_, exp) in self._data.items() if now >= exp]:
            del self._data[key]

    def set(self, key, value):
        self._purge()
        if key in self._data:
            del self._data[key]
        elif len(self._data) >= self.maxsize:
            self._data.popitem(last=False)
        self._data[key] = (value, self._clock() + self.ttl)

    def get(self, key, default=None):
        item = self._data.get(key, _MISSING)
        if item is _MISSING:
            return default
        value, expires_at = item
        if self._clock() >= expires_at:
            del self._data[key]
            return default
        self._data.move_to_end(key)
        return value

    def __contains__(self, key):
        return self.get(key, _MISSING) is not _MISSING

    def __len__(self):
        self._purge()
        return len(self._data)
PY
