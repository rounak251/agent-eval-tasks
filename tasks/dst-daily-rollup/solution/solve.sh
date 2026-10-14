#!/bin/bash
# Oracle: convert each timestamp with the zone's rules at that instant.
set -euo pipefail
APP_DIR="${APP_DIR:-/app}"
cat > "$APP_DIR/rollup/daily.py" <<'PY'
"""Per-day event counts in a customer's local time."""
from collections import Counter
from zoneinfo import ZoneInfo


def daily_counts(timestamps, tz_name):
    """Map local ``date`` -> number of events, for UTC ``timestamps``."""
    tz = ZoneInfo(tz_name)
    counts = Counter()
    for ts in timestamps:
        if ts.tzinfo is None:
            raise ValueError("timestamps must be timezone-aware")
        counts[ts.astimezone(tz).date()] += 1
    return dict(sorted(counts.items()))
PY
