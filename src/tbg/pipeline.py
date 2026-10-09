"""Orquestación determinista del flujo A: HU + TestModel → FrameSet."""

from __future__ import annotations

import hashlib

from . import coverage, gaps, lint, risk
from .generate.partition import build_frames
from .hu import UserStory
from .schemas import FrameSet, TestModel


def model_hash(model: TestModel) -> str:
    return hashlib.sha256(model.model_dump_json().encode()).hexdigest()[:12]


def analyze(story: UserStory, model: TestModel | None = None):
    findings = lint.lint(story)
    tags = set(model.feature_tags) if model else set(lint.suggest_tags(story))
    if model:
        tags |= set(lint.suggest_tags(story))
    return findings, sorted(tags), gaps.detect(story, tags, findings, model)


def with_suggested_tags(story: UserStory, model: TestModel) -> TestModel:
    """Los tags sugeridos por léxico se suman siempre: el LLM puede agregar, no quitar."""
    return model.model_copy(update={"feature_tags": sorted(set(model.feature_tags) | set(lint.suggest_tags(story)))})


def build(story: UserStory, model: TestModel) -> FrameSet:
    model = with_suggested_tags(story, model)
    findings, tags, gap_list = analyze(story, model)
    blocking = any(g.gap_class == "BLOQUEANTE" and g.status == "open" for g in gap_list)
    frames = [] if blocking else build_frames(model, gap_list)
    risk.assess(frames, tags)
    cov = coverage.compute(model, frames, gap_list)
    return FrameSet(story_id=model.story_id, title=model.title, module=model.module, model_hash=model_hash(model),
                    feature_tags=tags, findings=findings, gaps=gap_list, frames=frames, coverage=cov,
                    mode="analisis" if blocking else "completo")
