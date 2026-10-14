import random

import pytest

from feed import list_events


def page_all(events, limit):
    seen, cursor, calls = [], None, 0
    while True:
        page, cursor = list_events(events, limit, cursor)
        seen.extend(page)
        calls += 1
        assert calls <= len(events) + 2, "pagination does not terminate"
        if cursor is None:
            return seen
        assert isinstance(cursor, str)


def make_events(seed, n, distinct_ts):
    rng = random.Random(seed)
    ids = rng.sample(range(1, 10 * n), n)
    return [{"id": i, "ts": 1_700_000_000 + rng.randrange(distinct_ts), "kind": "x"} for i in ids]


@pytest.mark.parametrize("seed", range(5))
@pytest.mark.parametrize("limit", [1, 2, 3, 7, 50])
def test_every_event_exactly_once_with_heavy_ties(seed, limit):
    events = make_events(seed, 60, distinct_ts=6)
    seen = page_all(events, limit)
    ids = [e["id"] for e in seen]
    assert len(ids) == len(set(ids)), "duplicate events across pages"
    assert sorted(ids) == sorted(e["id"] for e in events), "events missing"


@pytest.mark.parametrize("limit", [1, 4, 9])
def test_newest_first_and_consistent_tie_order(limit):
    events = make_events(11, 40, distinct_ts=4)
    seen = page_all(events, limit)
    ts = [e["ts"] for e in seen]
    assert ts == sorted(ts, reverse=True)
    # tie order must not depend on page size or input order
    reference = [e["id"] for e in page_all(events, 1000)]
    assert [e["id"] for e in seen] == reference
    shuffled = events[:]
    random.Random(3).shuffle(shuffled)
    assert [e["id"] for e in page_all(shuffled, limit)] == reference


def test_distinct_timestamps_still_work():
    events = [{"id": i, "ts": 100 + i} for i in range(10)]
    seen = page_all(events, 3)
    assert [e["id"] for e in seen] == list(range(9, -1, -1))


def test_edge_cases():
    assert list_events([], 5) == ([], None)
    page, cursor = list_events([{"id": 1, "ts": 5}], 1)
    assert [e["id"] for e in page] == [1] and cursor is None
    with pytest.raises(ValueError):
        list_events([{"id": 1, "ts": 5}], 0)
