import csv
import io
import random
import subprocess
import sys
from decimal import ROUND_HALF_UP, Decimal

import pytest

HEADER = ["sku", "description", "quantity", "unit_price"]


def run(tmp_path, rows):
    p = tmp_path / "in.csv"
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(HEADER)
    w.writerows(rows)
    p.write_text(buf.getvalue())
    return subprocess.run([sys.executable, "-m", "invoicing", str(p)], capture_output=True, text=True)


def fmt(amount, style):
    neg = amount < 0
    a = abs(amount)
    body = f"{a:,.2f}" if style in ("comma", "dollar_comma") else f"{a:.2f}"
    if style.startswith("dollar"):
        body = "$" + body
    return ("-" if neg else "") + body


def test_sample_style_rows(tmp_path):
    rows = [
        ["A-100", "Annual licence", "1", "1,200.50"],
        ["B-220", "Support hours", "12", "$85.00"],
        ["C-310", "Onboarding", "", "2,500.00"],
        ["R-001", "Credit", "1", "-85.00"],
    ]
    r = run(tmp_path, rows)
    assert r.returncode == 0, r.stderr
    assert r.stdout.strip() == "4635.50"


@pytest.mark.parametrize("seed", range(4))
def test_random_exports_match_to_the_cent(tmp_path, seed):
    rng = random.Random(seed)
    rows, total = [], Decimal(0)
    for i in range(300):
        price = Decimal(rng.randrange(-50000, 900000)) / 100
        qty = rng.choice([None, 1, 2, 3, 10, 125])
        style = rng.choice(["plain", "comma", "dollar", "dollar_comma"])
        rows.append([f"S-{i}", "item, with comma", "" if qty is None else str(qty), fmt(price, style)])
        total += (qty or 1) * price
    r = run(tmp_path, rows)
    assert r.returncode == 0, r.stderr
    assert r.stdout.strip() == str(total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


@pytest.mark.parametrize("price,expected", [("1.005", "1.01"), ("2.675", "2.68"), ("-0.125", "-0.13")])
def test_half_up_rounding_of_fractional_prices(tmp_path, price, expected):
    # these sit exactly on the half-cent; binary floats round them the wrong way
    r = run(tmp_path, [["X", "fractional", "1", price]])
    assert r.returncode == 0, r.stderr
    assert r.stdout.strip() == expected


@pytest.mark.parametrize(
    "bad_row",
    [
        ["Z-9", "typo in price", "2", "12..50"],
        ["Z-9", "text quantity", "two", "10.00"],
        ["Z-9", "missing price", "1", ""],
        ["Z-9", "currency word", "1", "USD 10"],
    ],
)
def test_bad_row_fails_loudly_with_line_number(tmp_path, bad_row):
    rows = [["A", "ok", "1", "10.00"], ["B", "ok", "2", "5.00"], bad_row, ["C", "ok", "1", "1.00"]]
    r = run(tmp_path, rows)
    assert r.returncode != 0
    assert "4" in r.stderr  # header is line 1, bad row is line 4
    assert r.stdout.strip() == ""


def test_short_row_is_an_error(tmp_path):
    r = run(tmp_path, [["A", "ok", "1", "10.00"], ["B", "short"]])
    assert r.returncode != 0 and "3" in r.stderr
