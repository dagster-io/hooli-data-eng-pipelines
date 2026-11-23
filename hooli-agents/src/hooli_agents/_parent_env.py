"""Copy ENG_* and DAGSTER_PLUS_* variables from the parent process into this one.

The agent component starts the tool server with only a minimal environment, so the variables set on the
deployment never reach it. On Linux the parent's environment is readable from /proc.
"""

import os
from pathlib import Path

PREFIXES = ("ENG_", "DAGSTER_PLUS_")


def load(parent_environ: Path | None = None) -> list[str]:
    path = parent_environ or Path(f"/proc/{os.getppid()}/environ")
    try:
        raw = path.read_bytes()
    except OSError:
        return []
    copied = []
    for item in raw.split(b"\0"):
        name, _, value = item.decode(errors="replace").partition("=")
        if name.startswith(PREFIXES) and name not in os.environ:
            os.environ[name] = value
            copied.append(name)
    return copied
