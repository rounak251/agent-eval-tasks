"""A small LRU cache whose entries expire after a fixed time-to-live."""
import time
from collections import OrderedDict

_MISSING = object()


class TTLCache:
    def __init__(self, maxsize, ttl, clock=time.time):
        if maxsize < 1 or ttl <= 0:
            raise ValueError("maxsize must be >= 1 and ttl > 0")
        self.maxsize = maxsize
        self.ttl = ttl
        self._clock = clock
        self._data = OrderedDict()  # key -> (value, expires_at)

    def set(self, key, value):
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
        if self._clock() > expires_at:
            return default
        return value

    def __contains__(self, key):
        return self.get(key, _MISSING) is not _MISSING

    def __len__(self):
        return len(self._data)
