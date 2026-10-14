import os
import random
import subprocess
import sys
from collections import Counter
from datetime import date, datetime, timedelta, timezone

import pytest

from rollup import daily_counts

UTC = timezone.utc
# Fixed offsets taken from the zone rules, so the expectation never calls zoneinfo.
NY = [(datetime(2024, 3, 10, 7, tzinfo=UTC), -5), (datetime(2024, 11, 3, 6, tzinfo=UTC), -4), (None, -5)]
SYD = [(datetime(2024, 4, 6, 16, tzinfo=UTC), 11), (datetime(2024, 10, 5, 16, tzinfo=UTC), 10), (None, 11)]


def local_date(ts, table):
    for switch, hours in table:
        if switch is None or ts < switch:
            return (ts + timedelta(hours=hours)).date()


def random_stamps(seed, start, days, n):
    rng = random.Random(seed)
    return [start + timedelta(seconds=rng.randrange(days * 86400)) for _ in range(n)]


@pytest.mark.parametrize(
    "tz,table,start",
    [
        ("America/New_York", NY, datetime(2024, 3, 1, tzinfo=UTC)),
        ("America/New_York", NY, datetime(2024, 10, 25, tzinfo=UTC)),
        ("Australia/Sydney", SYD, datetime(2024, 3, 28, tzinfo=UTC)),
        ("Australia/Sydney", SYD, datetime(2024, 9, 28, tzinfo=UTC)),
    ],
)
def test_counts_across_dst_switch(tz, table, start):
    stamps = random_stamps(start.month * 31 + start.day, start, 20, 3000)
    expected = Counter(local_date(s, table) for s in stamps)
    assert daily_counts(stamps, tz) == dict(sorted(expected.items()))


def test_boundary_events_land_on_right_day():
    # 03:30 UTC on 2024-07-01 is 23:30 on 2024-06-30 in New York (EDT, -4),
    # and 04:30 UTC on 2024-01-15 is 23:30 on 2024-01-14 (EST, -5).
    stamps = [datetime(2024, 7, 1, 3, 30, tzinfo=UTC), datetime(2024, 1, 15, 4, 30, tzinfo=UTC)]
    assert daily_counts(stamps, "America/New_York") == {date(2024, 1, 14): 1, date(2024, 6, 30): 1}


def test_naive_timestamps_rejected():
    with pytest.raises(ValueError):
        daily_counts([datetime(2024, 6, 1)], "UTC")


def test_cli_output_format():
    lines = "2024-11-03T03:30:00+00:00\n2024-11-03T05:30:00+00:00\n2024-11-04T04:59:00+00:00\n"
    out = subprocess.run(
        [sys.executable, "-m", "rollup", "America/New_York"],
        input=lines, capture_output=True, text=True, check=True, cwd=os.getcwd(),
    ).stdout
    assert out.splitlines() == ["2024-11-02,1", "2024-11-03,2"]
