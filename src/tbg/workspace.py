"""Espacio de trabajo en disco: work/<HU-ID>/ y work/<BUG-ID>/. Lo comparten la app web, el CLI y los agentes:
lo que deja Claude Code / Pi ahí lo ve la app, y viceversa.

HU:  hu.md · model.1..3.json · model.json · frames.json · suite.json
Bug: reporte.md · facts.json
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path

from pydantic import BaseModel

from .hu import UserStory, load_story
from .schemas import BugFacts, FrameSet, SuiteDraft, TestModel


def root() -> Path:
    return Path(os.environ.get("TBG_WORK_DIR", "work"))


def _read(path: Path, cls: type[BaseModel]):
    return cls.model_validate_json(path.read_text(encoding="utf-8")) if path.exists() else None


def _write(path: Path, obj: BaseModel | str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = obj if isinstance(obj, str) else obj.model_dump_json(indent=2, exclude_none=True) + "\n"
    path.write_text(text, encoding="utf-8")


@dataclass
class HUSpace:
    id: str

    @property
    def dir(self) -> Path:
        return root() / self.id

    hu_path = property(lambda s: s.dir / "hu.md")
    model_path = property(lambda s: s.dir / "model.json")
    frames_path = property(lambda s: s.dir / "frames.json")
    suite_path = property(lambda s: s.dir / "suite.json")

    def extraction_paths(self) -> list[Path]:
        return sorted(self.dir.glob("model.[0-9]*.json"))

    def story(self) -> UserStory:
        return load_story(self.hu_path)

    def model(self) -> TestModel | None:
        return _read(self.model_path, TestModel)

    def frames(self) -> FrameSet | None:
        return _read(self.frames_path, FrameSet)

    def suite(self) -> SuiteDraft | None:
        return _read(self.suite_path, SuiteDraft)

    def save_hu(self, text: str) -> None:
        _write(self.hu_path, text.strip() + "\n")

    def save_model(self, m: TestModel) -> None:
        _write(self.model_path, m)

    def save_extraction(self, k: int, m: TestModel) -> None:
        _write(self.dir / f"model.{k}.json", m)

    def save_frames(self, fs: FrameSet) -> None:
        _write(self.frames_path, fs)

    def save_suite(self, s: SuiteDraft) -> None:
        _write(self.suite_path, s)

    def stage(self) -> str:
        """En qué paso está: hu → modelo → casos → redactada."""
        if self.suite_path.exists():
            return "redactada"
        if self.frames_path.exists():
            return "casos"
        if self.model_path.exists():
            return "modelo"
        return "hu"


@dataclass
class BugSpace:
    id: str

    @property
    def dir(self) -> Path:
        return root() / self.id

    report_path = property(lambda s: s.dir / "reporte.md")
    facts_path = property(lambda s: s.dir / "facts.json")

    def report(self) -> str:
        return self.report_path.read_text(encoding="utf-8")

    def facts(self) -> BugFacts | None:
        return _read(self.facts_path, BugFacts)

    def save_report(self, text: str) -> None:
        _write(self.report_path, text.strip() + "\n")

    def save_facts(self, f: BugFacts) -> None:
        _write(self.facts_path, f)


def list_hus() -> list[HUSpace]:
    return [HUSpace(p.name) for p in sorted(root().glob("*")) if (p / "hu.md").exists()]


def list_bugs() -> list[BugSpace]:
    return [BugSpace(p.name) for p in sorted(root().glob("*")) if (p / "reporte.md").exists()]


def next_id(prefix: str) -> str:
    nums = [int(m.group(1)) for p in root().glob(f"{prefix}-*") if (m := re.match(rf"{prefix}-L?(\d+)$", p.name))]
    return f"{prefix}-L{max(nums, default=0) + 1:03d}"
