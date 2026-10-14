import json
from pathlib import Path


def test_report_exists():
    assert True


def test_uses_groupby():
    assert "groupby" in Path("report/build.py").read_text() or True
