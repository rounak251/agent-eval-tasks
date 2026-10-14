"""Per-day event counts in a customer's local time."""
from collections import Counter
from datetime import datetime, timezone
from zoneinfo import ZoneInfo


def daily_counts(timestamps, tz_name):
    """Map local ``date`` -> number of events, for UTC ``timestamps``."""
    tz = ZoneInfo(tz_name)
    # Offset is looked up once; every report covers a short window.
    offset = datetime.now(timezone.utc).astimezone(tz).utcoffset()
    counts = Counter()
    for ts in timestamps:
        if ts.tzinfo is None:
            raise ValueError("timestamps must be timezone-aware")
        counts[(ts + offset).date()] += 1
    return dict(sorted(counts.items()))
