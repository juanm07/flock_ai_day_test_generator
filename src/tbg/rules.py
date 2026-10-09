"""Carga de reglas YAML (fuente de verdad editable por el equipo de QA, sin tocar código)."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

DEFAULT_RULES_DIR = Path(__file__).resolve().parents[2] / "rules"


def rules_dir() -> Path:
    return Path(os.environ.get("TBG_RULES_DIR", DEFAULT_RULES_DIR))


@lru_cache(maxsize=None)
def load(name: str) -> Any:
    path = rules_dir() / f"{name}.yaml"
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)
