Our in-process cache (`TTLCache` in `/app/cachelib/ttl.py`) is behaving strangely in production. Hot keys that are read constantly keep getting evicted, while entries that expired long ago seem to sit around and push live entries out. `len(cache)` also reports more items than we can actually `get`. We started seeing it after a server's clock got corrected by NTP.

Expected behaviour:
- Entries expire `ttl` seconds after they were last written, measured with the clock passed in (the default should not jump when the wall clock is adjusted).
- When the cache is full, expired entries go first. If a live entry has to be evicted, it is the least recently used one, where both `get` hits and `set` count as use.
- `len()`, `in` and `get` only ever see live entries.

Please fix the class. Keep the constructor and method signatures the same; other code depends on them.
