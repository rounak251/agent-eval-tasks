"""Quality gate for an agent task. Run: python tools/validate_task.py tasks/<name> [...]

Checks, in the order a careful reviewer would:
  1. layout         instruction.md, task.toml, environment/, solution/solve.sh, tests/test_outputs.py exist
  2. no-op fails    the untouched environment must FAIL the verifier (no pass-by-default)
  3. oracle passes  the reference fix must PASS the verifier on every one of N runs (no flakiness)
  4. no leakage     nothing from tests/ or solution/ is visible inside environment/
  5. test quality   tests exercise behaviour, never grep or parse the agent's source
  6. instruction    reads like a human request: short, no solution walkthrough or hint sections
  7. pinning        Dockerfile base image and pip installs are pinned to exact versions
"""
import argparse
import hashlib
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HINT_HEADINGS = re.compile(r"^#+\s*(hints?|suggested approach|solution|implementation notes|steps)\b", re.I | re.M)
SOURCE_PEEKING = re.compile(r"inspect\.getsource|ast\.parse|\.py['\"]\)?\.(read_text|read_bytes)|open\([^)]*\.py['\"]|\bgrep\s")
EXPECTED_FILES = re.compile(r"(expected|golden|answer|solution)[^/]*\.(json|csv|txt|out)$", re.I)


def run_verifier(task, apply_oracle):
    work = Path(tempfile.mkdtemp(prefix="task_"))
    try:
        app = work / "app"
        shutil.copytree(task / "environment" / "app", app)
        env = {**os.environ, "APP_DIR": str(app), "PYTHONPATH": str(app), "PYTHONDONTWRITEBYTECODE": "1"}
        if apply_oracle:
            subprocess.run(["bash", str(task / "solution" / "solve.sh")], env=env, check=True)
        r = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", str(task / "tests" / "test_outputs.py")],
            cwd=app, env=env, capture_output=True, text=True, timeout=300,
        )
        return r.returncode == 0, r.stdout.strip().splitlines()[-1] if r.stdout.strip() else r.stderr[-300:]
    finally:
        shutil.rmtree(work, ignore_errors=True)


def oracle_files(task):
    """Bodies the oracle writes (heredocs inside solve.sh)."""
    text = (task / "solution" / "solve.sh").read_text()
    return re.findall(r"<<'(\w+)'\n(.*?)\n\1\n", text, re.S)


def check(task, runs):
    problems, notes = [], []
    need = ["instruction.md", "task.toml", "environment/Dockerfile", "environment/app",
            "solution/solve.sh", "tests/test_outputs.py"]
    missing = [n for n in need if not (task / n).exists()]
    if missing:
        return [f"missing {', '.join(missing)}"], notes

    ok, tail = run_verifier(task, apply_oracle=False)
    notes.append(f"no-op: {'PASS' if ok else 'fail'} ({tail})")
    if ok:
        problems.append("verifier passes on the unmodified environment")

    for i in range(runs):
        ok, tail = run_verifier(task, apply_oracle=True)
        if not ok:
            problems.append(f"oracle failed on run {i + 1}: {tail}")
            break
    else:
        notes.append(f"oracle: pass x{runs} ({tail})")

    env_files = [p for p in (task / "environment").rglob("*") if p.is_file()]
    env_hashes = {hashlib.sha256(p.read_bytes()).hexdigest() for p in env_files}
    for _, body in oracle_files(task):
        if hashlib.sha256((body + "\n").encode()).hexdigest() in env_hashes:
            problems.append("an oracle-written file already exists verbatim in environment/")
    for p in env_files:
        rel = p.relative_to(task / "environment").as_posix()
        if EXPECTED_FILES.search(rel) or "test_outputs" in rel or rel.startswith("app/tests"):
            problems.append(f"possible ground truth visible to the agent: {rel}")

    tests = (task / "tests" / "test_outputs.py").read_text()
    if SOURCE_PEEKING.search(tests):
        problems.append("tests read the agent's source instead of checking behaviour")
    if len(re.findall(r"^def test_", tests, re.M)) < 3:
        problems.append("fewer than 3 test functions")

    instr = (task / "instruction.md").read_text()
    if HINT_HEADINGS.search(instr):
        problems.append("instruction contains a hint / solution section")
    if len(instr) > 2500:
        problems.append(f"instruction is {len(instr)} chars; keep it a focused request")
    if len(re.findall(r"^#+ ", instr, re.M)) > 2:
        problems.append("instruction is a heavily structured document, not a request")

    docker = (task / "environment" / "Dockerfile").read_text()
    base = re.search(r"^FROM\s+(\S+)", docker, re.M)
    if not base or not re.search(r"(@sha256:|:\d+\.\d+\.\d+)", base.group(1)):
        problems.append("base image is not pinned to an exact version")
    for spec in re.findall(r"pip install[^\n]*", docker):
        for pkg in spec.split()[2:]:
            if not pkg.startswith("-") and "==" not in pkg:
                problems.append(f"unpinned pip package: {pkg}")
    return problems, notes


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tasks", nargs="+", type=Path)
    ap.add_argument("--runs", type=int, default=3)
    args = ap.parse_args()
    failed = 0
    for task in args.tasks:
        task = task.resolve()
        problems, notes = check(task, args.runs)
        status = "OK  " if not problems else "FAIL"
        print(f"[{status}] {task.name}")
        for n in notes:
            print(f"       {n}")
        for p in problems:
            print(f"     - {p}")
        failed += bool(problems)
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
