import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def validate(path):
    return subprocess.run(
        [sys.executable, str(ROOT / "tools" / "validate_task.py"), "--runs", "2", str(path)],
        capture_output=True, text=True,
    )


def test_all_shipped_tasks_pass_the_gate():
    r = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "validate_task.py"), "--runs", "2",
         *map(str, sorted((ROOT / "tasks").iterdir()))],
        capture_output=True, text=True,
    )
    assert r.returncode == 0, r.stdout


def test_flawed_task_is_rejected_for_each_classic_problem():
    r = validate(ROOT / "examples" / "flawed-report-task")
    assert r.returncode == 1
    out = r.stdout
    for finding in [
        "verifier passes on the unmodified environment",
        "possible ground truth visible to the agent: app/expected_report.json",
        "instruction contains a hint / solution section",
        "base image is not pinned",
        "unpinned pip package: pytest",
        "fewer than 3 test functions",
        "tests read the agent's source instead of checking behaviour",
    ]:
        assert finding in out, out
