# agent-eval-tasks

Bug-fix tasks for evaluating AI coding agents, plus the quality gate I use to review
tasks before they are allowed into an eval set.

The tasks are small on purpose. Each one is a bug that a careless fix gets *almost* right,
and the verifier is built to separate a real fix from a plausible-looking one.

```
$ python tools/validate_task.py tasks/*
[OK  ] dst-daily-rollup
       no-op: fail (6 failed, 1 passed)
       oracle: pass x3 (7 passed)
[OK  ] feed-pagination-ties
       no-op: fail (27 failed, 3 passed)
       oracle: pass x3 (30 passed)
[OK  ] invoice-totals-csv
       no-op: fail (13 failed)
       oracle: pass x3 (13 passed)
[OK  ] ttl-lru-cache
       no-op: fail (4 failed, 3 passed)
       oracle: pass x3 (7 passed)
```

## Task format

```
tasks/<name>/
  instruction.md        what the agent sees: a bug report written the way a user would write it
  task.toml             difficulty, category, timeouts
  environment/          Dockerfile (pinned) + the broken app copied to /app
  solution/solve.sh     reference fix (oracle), never visible to the agent
  tests/test_outputs.py hidden verifier, run after the agent finishes
```

## The tasks

| Task | Symptom in the bug report | Real cause | What a careless fix does | How the verifier tells them apart |
|---|---|---|---|---|
| `feed-pagination-ties` | Feed skips events when scrolling during busy periods | Cursor keyed on `ts` alone; rows sharing a timestamp across a page boundary are dropped by `ts < cursor` | Switches to `<=`, which duplicates rows instead of skipping them | Pages through randomised data with heavy timestamp ties at page sizes 1–50; checks exactly-once delivery and that tie order is independent of page size and input order |
| `dst-daily-rollup` | Daily counts wrong for weeks around clock changes | UTC offset looked up once ("now") and applied to every event | Hard-codes the offset for the customer's zone, or uses the offset of the first event | Random events across both DST switches in two hemispheres; expected dates come from a fixed offset table, not from `zoneinfo`, so the verifier does not share code with the fix |
| `ttl-lru-cache` | Hot keys evicted, dead entries linger, `len()` too high after an NTP correction | `get` doesn't refresh recency; expired entries take capacity; wall-clock default | Fixes recency but not expiry-aware eviction, or keeps `time.time` | Fake clock for exact expiry boundaries; reloads the module under a jumping wall clock; 3,000 random operations against a reference model |
| `invoice-totals-csv` | Totals a few thousand below finance's spreadsheet | `float()` fails on `"1,200.50"` and blank quantities, and the error is swallowed | Strips commas but keeps floats, so cents round wrong; or still skips bad rows | Randomised exports in four price formats, checked to the cent with `Decimal`; half-cent cases where floats round the wrong way; bad rows must fail with the line number |

## The quality gate (`tools/validate_task.py`)

| Check | Why it matters |
|---|---|
| No-op must fail | A verifier that passes on the broken repo measures nothing |
| Oracle passes on every one of N runs | A flaky oracle makes every score noise |
| No ground truth in `environment/` | Expected outputs or the fixed file in view means the agent can copy instead of solve |
| Tests check behaviour, not source | Grepping for a helper name rewards matching the author's implementation, not correctness |
| Instruction reads like a human request | No "Suggested approach" walkthroughs, checklists or step-by-step hints |
| Exact version pins | A task that installs "latest" at runtime is a different task next month |

`examples/flawed-report-task` is a deliberately bad submission, the kind a reviewer sees
in practice. It has an expected output file in the image, a solution outline in the
prompt, a verifier that only asserts `True`, and unpinned dependencies. The gate rejects
it on 8 counts, and `tests/test_validator.py` locks that behaviour in.

## Run it

```
pip install pytest
python tools/validate_task.py tasks/*      # gate every task
pytest -q tests                            # gate + flawed-task regression
docker build -t feed tasks/feed-pagination-ties/environment   # agent environment
```

## Limitations

- Four tasks is a small set. It shows the method, not a benchmark you could rank agents with.
- All four bugs are single-repository Python logic bugs. There are no multi-service, front-end or performance tasks yet.
- The gate checks structure and runs the oracle and no-op. It cannot prove a verifier has no loophole. That still needs a human reviewer trying to break it.
- The tasks have not yet been run against a range of real coding agents to measure how hard they are.

MIT licensed.
