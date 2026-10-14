import csv
import sys


def line_total(row):
    qty = float(row["quantity"])
    price = float(row["unit_price"].replace("$", ""))
    return qty * price


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 1:
        print("usage: python -m invoicing <file.csv>", file=sys.stderr)
        return 2
    total = 0.0
    with open(argv[0], newline="") as f:
        for row in csv.DictReader(f):
            try:
                total += line_total(row)
            except (ValueError, TypeError):
                continue
    print(f"{total:.2f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
