import inspect
import random

import pytest

from cachelib import TTLCache


class FakeClock:
    def __init__(self, t=1000.0):
        self.t = t

    def __call__(self):
        return self.t


def test_get_hit_counts_as_use():
    clk = FakeClock()
    c = TTLCache(maxsize=2, ttl=100, clock=clk)
    c.set("a", 1); c.set("b", 2)
    assert c.get("a") == 1
    c.set("c", 3)  # must evict b, the least recently used
    assert c.get("a") == 1 and c.get("c") == 3 and c.get("b") is None


def test_expired_entries_are_evicted_before_live_ones():
    clk = FakeClock()
    c = TTLCache(maxsize=3, ttl=10, clock=clk)
    c.set("live1", 1)
    clk.t += 5
    c.set("old", 2)
    c.set("live2", 3)
    clk.t += 6  # live1 expired at t+10; old and live2 alive until t+15
    c.set("new", 4)
    assert c.get("old") == 2 and c.get("live2") == 3 and c.get("new") == 4
    clk.t += 5  # old and live2 expire now
    c.set("x", 5); c.set("y", 6)
    assert c.get("new") == 4 and c.get("x") == 5 and c.get("y") == 6


def test_len_contains_get_only_see_live_entries():
    clk = FakeClock()
    c = TTLCache(maxsize=10, ttl=10, clock=clk)
    for i in range(5):
        c.set(i, i)
    clk.t += 10  # exactly ttl after the write: expired
    assert len(c) == 0 and 0 not in c and c.get(0, "d") == "d"
    c.set("k", "v")
    assert len(c) == 1 and "k" in c


def test_rewrite_resets_ttl():
    clk = FakeClock()
    c = TTLCache(maxsize=2, ttl=10, clock=clk)
    c.set("a", 1)
    clk.t += 8
    c.set("a", 2)
    clk.t += 8
    assert c.get("a") == 2


def test_default_clock_is_immune_to_wall_clock_jumps():
    import importlib
    import time

    import cachelib.ttl as ttl_mod

    real_time = time.time
    wall = {"offset": 0.0}
    time.time = lambda: real_time() + wall["offset"]
    try:
        importlib.reload(ttl_mod)  # rebind any default captured at import time
        c = ttl_mod.TTLCache(maxsize=2, ttl=60)
        c.set("a", 1)
        wall["offset"] = 3600.0  # NTP steps the wall clock forward an hour
        assert c.get("a") == 1
        wall["offset"] = -3600.0  # and back
        c.set("b", 2)
        assert c.get("b") == 2 and c.get("a") == 1
    finally:
        time.time = real_time
        importlib.reload(ttl_mod)


def test_signature_unchanged():
    params = list(inspect.signature(TTLCache).parameters)
    assert params == ["maxsize", "ttl", "clock"]
    with pytest.raises(ValueError):
        TTLCache(0, 1)


def test_matches_reference_model_on_random_ops():
    rng = random.Random(7)
    clk = FakeClock()
    c = TTLCache(maxsize=4, ttl=5, clock=clk)
    model = {}  # key -> (value, expires_at, last_use)
    tick = 0
    for _ in range(3000):
        tick += 1
        clk.t += rng.choice([0, 0, 0.5, 1, 2])
        key = rng.randrange(8)
        model = {k: v for k, v in model.items() if clk.t < v[1]}
        if rng.random() < 0.5:
            val = rng.randrange(100)
            if key not in model and len(model) >= 4:
                lru = min(model, key=lambda k: model[k][2])
                del model[lru]
            model[key] = (val, clk.t + 5, tick)
            c.set(key, val)
        else:
            exp = model.get(key)
            got = c.get(key, None)
            assert got == (exp[0] if exp else None)
            if exp:
                model[key] = (exp[0], exp[1], tick)
        assert len(c) == len(model)
