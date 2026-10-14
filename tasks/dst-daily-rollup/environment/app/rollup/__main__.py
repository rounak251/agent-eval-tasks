import sys
from datetime import datetime

from .daily import daily_counts


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 1:
        print("usage: python -m rollup <iana-tz> < timestamps.txt", file=sys.stderr)
        return 2
    stamps = [datetime.fromisoformat(line.strip()) for line in sys.stdin if line.strip()]
    for day, n in daily_counts(stamps, argv[0]).items():
        print(f"{day.isoformat()},{n}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
