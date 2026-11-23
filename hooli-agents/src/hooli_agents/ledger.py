"""A record of what the agents' tools actually did, so run outcomes come from facts, not from the model's prose."""

import contextlib
import fcntl
import json
import os
import time
from pathlib import Path

VAR_DIR = Path(os.environ.get("ENG_VAR_DIR", Path(__file__).resolve().parents[2] / "var"))
PATH = VAR_DIR / "ledger.jsonl"


def record(kind: str, **fields) -> None:
    PATH.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps({"ts": time.time(), "kind": kind, **fields})
    with open(PATH.with_suffix(".lock"), "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        with open(PATH, "a") as f:
            f.write(line + "\n")


def since(start: float) -> list[dict]:
    if not PATH.exists():
        return []
    rows = []
    for line in PATH.read_text().splitlines():
        with contextlib.suppress(ValueError):
            row = json.loads(line)
            if row["ts"] >= start:
                rows.append(row)
    return rows
