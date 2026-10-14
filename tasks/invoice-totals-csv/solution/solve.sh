#!/bin/bash
# Oracle: Decimal parsing that accepts currency formatting, blank qty = 1, strict errors.
set -euo pipefail
APP_DIR="${APP_DIR:-/app}"
cat > "$APP_DIR/invoicing/__main__.py" <<'PY'
import csv
import re
import sys
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

_MONEY = re.compile(r"^-?\$?-?\d{1,3}(,\d{3})*(\.\d+)?$|^-?\$?-?\d+(\.\d+)?$")


class RowError(ValueError):
    pass


def parse_money(text):
    s = text.strip()
    if not _MONEY.match(s) or s.count("-") > 1:
        raise RowError(f"bad price {text!r}")
    return Decimal(s.replace("$", "").replace(",", ""))


def parse_qty(text):
    s = (text or "").strip()
    if s == "":
        return Decimal(1)
    try:
        q = Decimal(s.replace(",", ""))
    except InvalidOperation:
        raise RowError(f"bad quantity {text!r}") from None
    if not q.is_finite():
        raise RowError(f"bad quantity {text!r}")
    return q


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 1:
        print("usage: python -m invoicing <file.csv>", file=sys.stderr)
        return 2
    total = Decimal(0)
    with open(argv[0], newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            line = reader.line_num
            try:
                if None in row or row.get("unit_price") is None:
                    raise RowError("wrong number of columns")
                total += parse_qty(row["quantity"]) * parse_money(row["unit_price"])
            except RowError as e:
                print(f"line {line}: {e}", file=sys.stderr)
                return 1
    print(total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
    return 0


if __name__ == "__main__":
    sys.exit(main())
PY
