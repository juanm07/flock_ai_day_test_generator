from pathlib import Path

import pytest

from tbg.hu import load_story, parse_story
from tbg.schemas import TestModel

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def story():
    return load_story(ROOT / "ejemplos" / "hu-ejemplo.md")


@pytest.fixture
def model():
    return TestModel.model_validate_json((ROOT / "ejemplos" / "hu-101.model.json").read_text(encoding="utf-8"))


@pytest.fixture
def make_story():
    return parse_story
