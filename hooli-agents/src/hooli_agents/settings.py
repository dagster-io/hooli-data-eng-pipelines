"""Settings: ENG_<KEY> environment variables, then an optional settings.local.json (or ENG_SETTINGS)."""

import json
import os
from functools import lru_cache
from pathlib import Path

_DEFAULT = Path(__file__).resolve().parents[2] / "settings.local.json"


@lru_cache(maxsize=1)
def load() -> dict:
    path = Path(os.environ.get("ENG_SETTINGS", _DEFAULT))
    return json.loads(path.read_text()) if path.exists() else {}


def get(key: str, default=None):
    return os.environ.get("ENG_" + key.upper(), load().get(key, default))


def shadow() -> bool:
    """Practice mode: tools record what they would file and change nothing."""
    return str(get("shadow", "")).strip().lower() not in ("", "0", "false", "no", "off")
