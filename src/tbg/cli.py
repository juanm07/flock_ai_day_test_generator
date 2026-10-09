"""tbg · Test & Bug Generator (Flock QA).

Para empezar: `tbg asistente` (guiado en la terminal) o `tbg ui` (app web). Ambos pueden usar una IA si la
configurás, y funcionan sin ella. El resto de los comandos son el núcleo determinista (nunca llaman a un LLM):
los usan los agentes (Claude Code, Pi…) o se encadenan para automatizar. Entradas y salidas: JSON/markdown.
"""

from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path
from typing import Optional

import typer
from pydantic import ValidationError

from . import lint as lint_mod
from . import modelcheck, pipeline
from .hu import load_story
from .schemas import SCHEMAS, Answer, Bounds, FrameSet, SuiteDraft, TestModel

app = typer.Typer(add_completion=False, no_args_is_help=True, help=__doc__)

for _s in (sys.stdout, sys.stderr):  # consola de Windows: forzar UTF-8 (ñ, tildes, ✓)
    try:
        _s.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except Exception:
        pass


def _out(obj) -> None:
    typer.echo(json.dumps(obj, ensure_ascii=False, indent=2))


def _load_model(path: Path) -> TestModel:
    try:
        return TestModel.model_validate_json(path.read_text(encoding="utf-8"))
    except ValidationError as e:
        typer.echo(f"✗ {path} no cumple el schema test-model:\n{e}", err=True)
        raise typer.Exit(2)


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


# ---------------------------------------------------------------------------


@app.command(rich_help_panel="Empezar acá")
def asistente(archivo: Optional[Path] = typer.Argument(None, help="HU o reporte (.md/.txt). Sin archivo, se pega."),
              es_bug: Optional[bool] = typer.Option(None, "--bug/--hu", help="Tipo de entrada (si no, pregunta)"),
              out: Path = typer.Option(Path("salidas"), "-o", "--out", help="Carpeta de resultados")) -> None:
    """Asistente guiado paso a paso (HU → casos de prueba, o reporte → bug). Sin flags ni archivos JSON."""
    from . import wizard

    wizard.run(archivo, es_bug, out)


@app.command(rich_help_panel="Empezar acá")
def ui(port: int = typer.Option(8765, "--port"), open_browser: bool = typer.Option(True, "--open/--no-open")) -> None:
    """Abre la app web local para QA/PO (pegar HU o bug, responder preguntas, revisar casos, exportar)."""
    try:
        import uvicorn
    except ImportError:
        typer.echo("✗ Falta instalar la app: pip install -e \".[ui]\"", err=True)
        raise typer.Exit(1)
    from . import llm

    url = f"http://127.0.0.1:{port}"
    typer.echo(f"tbg ui → {url}   (IA: {llm.config().label if llm.available() else 'sin LLM, modo agente'})  Ctrl+C para salir")
    if open_browser:
        import threading
        import webbrowser

        threading.Timer(1.2, lambda: webbrowser.open(url)).start()
    uvicorn.run("tbg.web.app:app", host="127.0.0.1", port=port, log_level="warning")


@app.command(rich_help_panel="Núcleo (agentes y automatización)")
def schema(name: str = typer.Argument(..., help="test-model | suite | bug-facts")) -> None:
    """Imprime el JSON Schema que el agente debe respetar."""
    if name not in SCHEMAS:
        raise typer.BadParameter(f"opciones: {', '.join(SCHEMAS)}")
    _out(SCHEMAS[name].model_json_schema())


@app.command("lint-hu", rich_help_panel="Núcleo (agentes y automatización)")
def lint_hu(hu: Path, as_json: bool = typer.Option(False, "--json")) -> None:
    """Lint determinista de la HU: smells, Quality User Story, tags sugeridos y lagunas por reglas."""
    story = load_story(hu)
    findings, tags, gaps = pipeline.analyze(story)
    suggested = lint_mod.suggest_tags(story)
    if as_json:
        _out({"story": {"id": story.id, "title": story.title, "role": story.role, "want": story.want,
                        "so_that": story.so_that, "acceptance_criteria": story.acceptance_criteria},
              "suggested_tags": suggested, "findings": [f.model_dump() for f in findings],
              "gaps": [g.model_dump() for g in gaps]})
        return
    typer.echo(f"{story.id} — {story.title}  ({len(story.acceptance_criteria)} CAs)")
    typer.echo("Tags sugeridos: " + ", ".join(f"{t} («{w}»)" for t, w in suggested.items()))
    typer.echo(f"\nHallazgos de lint: {len(findings)}")
    for f in findings:
        typer.echo(f"  [{f.rule}] {f.location}: «{f.text}» — {f.message}")
    _print_gaps(gaps)


def _print_gaps(gaps) -> None:
    typer.echo(f"\nLagunas: {len(gaps)}  (preguntas al PO: {sum(g.asked for g in gaps)})")
    for g in gaps:
        mark = "?" if g.asked else ("✓" if g.status != "open" else "·")
        extra = f" → {g.answer}" if g.answer else ""
        typer.echo(f"  {mark} [{g.gap_class}] {g.id}: {g.question}{extra}")


@app.command("check-model", rich_help_panel="Núcleo (agentes y automatización)")
def check_model(model: Path, hu: Path = typer.Option(..., "--hu")) -> None:
    """Valida el TestModel extraído por el LLM: schema, citas contra la HU, vocabulario, referencias."""
    m = _load_model(model)
    story = load_story(hu)
    issues = modelcheck.check(m, story)
    for i in issues:
        typer.echo(f"  {'✗' if i.level == 'error' else '!'} {i.path}: {i.message}")
    _, _, gaps = pipeline.analyze(story, m)
    _print_gaps(gaps)
    errors = [i for i in issues if i.level == "error"]
    typer.echo(f"\n{'✗' if errors else '✓'} {len(errors)} errores, {len(issues) - len(errors)} advertencias")
    raise typer.Exit(1 if errors else 0)


@app.command(rich_help_panel="Núcleo (agentes y automatización)")
def consensus(models: list[Path], hu: Path = typer.Option(..., "--hu"),
              out: Path = typer.Option(..., "-o", "--out")) -> None:
    """Self-consistency: fusiona N extracciones independientes del TestModel por voto mayoritario (determinista)."""
    from .consensus import merge

    story = load_story(hu)
    valid = []
    for path in models:
        m = _load_model(path)
        errors = [i for i in modelcheck.check(m, story) if i.level == "error"]
        if errors:
            typer.echo(f"  ✗ {path}: {len(errors)} errores ({errors[0].message}); se excluye del voto", err=True)
        else:
            valid.append(m)
    if len(valid) < 2:
        typer.echo("✗ Se necesitan al menos 2 extracciones válidas (idealmente 3).", err=True)
        raise typer.Exit(1)
    r = merge(valid)
    _write(out, r.model.model_dump_json(indent=2, exclude_none=True) + "\n")
    typer.echo(f"✓ {out}: consenso de {r.n} extracciones · {r.kept_params} parámetros · "
               f"{sum(len(p.choices) for p in r.model.parameters)} particiones · unanimidad {r.agreement:.0%}")
    if r.minorities:
        typer.echo("\nMinoritarios (vistos por menos de la mitad; revisar con el usuario si alguno debería entrar):")
        for x in r.minorities:
            typer.echo(f"  · {x.kind} {x.name} ({x.votes}/{x.total}){' — ' + x.detail if x.detail else ''}")


@app.command("po-form", rich_help_panel="Núcleo (agentes y automatización)")
def po_form(model: Path, hu: Path = typer.Option(..., "--hu"), out: Path = typer.Option(..., "-o", "--out")) -> None:
    """Genera el formulario YAML para el PO: preguntas abiertas + campos estructurados de límites."""
    from .po import build_form

    m = pipeline.with_suggested_tags(load_story(hu), _load_model(model))
    _, _, gaps = pipeline.analyze(load_story(hu), m)
    _write(out, build_form(m, gaps))
    typer.echo(f"✓ {out}: {sum(g.asked for g in gaps)} preguntas. Mandáselo al PO y aplicalo con `tbg po-apply`.")


@app.command("po-apply", rich_help_panel="Núcleo (agentes y automatización)")
def po_apply(form: Path, model: Path, hu: Path = typer.Option(..., "--hu")) -> None:
    """Aplica el formulario completado por el PO al TestModel (respuestas y límites). Determinista."""
    from .po import apply_form

    story = load_story(hu)
    original = _load_model(model)
    m = pipeline.with_suggested_tags(story, original)
    _, _, gaps = pipeline.analyze(story, m)
    try:
        res = apply_form(form.read_text(encoding="utf-8"), m, gaps)
    except ValueError as e:
        typer.echo(f"✗ {e}", err=True)
        raise typer.Exit(1)
    m.feature_tags = original.feature_tags  # no persistir los tags sugeridos: se recalculan siempre
    _write(model, m.model_dump_json(indent=2, exclude_none=True) + "\n")
    typer.echo(f"✓ {model}: {len(res.answers)} respuestas, {len(res.bounds)} límites")
    for b in res.bounds:
        typer.echo(f"  límites → {b}")
    if res.skipped:
        typer.echo(f"  sin responder (siguen como [SUPUESTO]): {', '.join(res.skipped)}")
    typer.echo("Siguiente: `tbg generate` (los frames ya redactados conservan su frame_id).")


@app.command(rich_help_panel="Núcleo (agentes y automatización)")
def answer(model: Path, gap_id: str, value: str, by: str = typer.Option("PO", help="PO | default")) -> None:
    """Registra la respuesta a una laguna en el TestModel (loop interactivo con el PO)."""
    m = _load_model(model)
    m.answers[gap_id] = Answer(value=value, by=by)  # type: ignore[arg-type]
    _write(model, m.model_dump_json(indent=2, exclude_none=True) + "\n")
    typer.echo(f"✓ {gap_id} = {value!r} ({by})")


@app.command("set-bounds", rich_help_panel="Núcleo (agentes y automatización)")
def set_bounds(model: Path, param: str, min: Optional[float] = typer.Option(None, "--min"),
               max: Optional[float] = typer.Option(None, "--max"), unit: str = typer.Option("chars"),
               origin: str = typer.Option("PO", help="HU | PO | SUPUESTO")) -> None:
    """Define los límites de un parámetro (habilita los casos de valores límite)."""
    m = _load_model(model)
    p = next((p for p in m.parameters if p.name == param), None)
    if p is None:
        raise typer.BadParameter(f"parámetro inexistente: {param}")
    p.bounds = Bounds(min=min, max=max, unit=unit, origin=origin)  # type: ignore[arg-type]
    p.bounds_relevant = True
    _write(model, m.model_dump_json(indent=2, exclude_none=True) + "\n")
    fmt = lambda v: "" if v is None else f"{v:g}"
    typer.echo(f"✓ {param}: {fmt(min)}–{fmt(max)} {unit} ({origin})")


@app.command(rich_help_panel="Núcleo (agentes y automatización)")
def generate(model: Path, hu: Path = typer.Option(..., "--hu"), out: Path = typer.Option(..., "-o", "--out")) -> None:
    """Genera los frames (qué probar, con qué datos, qué se espera) + riesgo + cobertura. 100% determinista."""
    m = _load_model(model)
    story = load_story(hu)
    errors = [i for i in modelcheck.check(m, story) if i.level == "error"]
    if errors:
        for i in errors:
            typer.echo(f"  ✗ {i.path}: {i.message}", err=True)
        typer.echo("✗ El modelo tiene errores: corregir y correr `tbg check-model` antes de generar.", err=True)
        raise typer.Exit(1)
    fs = pipeline.build(story, m)
    _write(out, fs.model_dump_json(indent=2) + "\n")
    c = fs.coverage
    typer.echo(f"✓ {out}: {len(fs.frames)} frames · modo {fs.mode} · CAs {c.ac_percent:g}% · "
               f"pares {c.pairs_covered}/{c.pairs_total} · límites {c.boundaries_covered}/{c.boundaries_total} · "
               f"preguntas al PO {sum(g.asked for g in fs.gaps)}")
    typer.echo("\nFrames a redactar (un caso por frame, en suite.json):")
    for f in fs.frames:
        tags = "".join([" [SUPUESTO]" if f.supuestos else "", " [exploratorio]" if f.exploratory else "", " [humo]" if f.smoke else ""])
        typer.echo(f"  {f.case_id} {f.frame_id} {f.type:<12} {f.priority:<5} {','.join(f.ac_refs) or '—':<12} {f.title_hint}{tags}")


@app.command(rich_help_panel="Núcleo (agentes y automatización)")
def validate(suite: Path, frames: Path = typer.Option(..., "--frames")) -> None:
    """Gate de calidad sobre la redacción del agente. Exit 1 si falla un ítem crítico."""
    from .validate import validate as run

    fs = FrameSet.model_validate_json(frames.read_text(encoding="utf-8"))
    try:
        sd = SuiteDraft.model_validate_json(suite.read_text(encoding="utf-8"))
    except ValidationError as e:
        typer.echo(f"✗ {suite} no cumple el schema suite:\n{e}", err=True)
        raise typer.Exit(2)
    report = run(fs, sd)
    for c in report.checks:
        typer.echo(f"  {'✓' if c.passed else '✗'} {c.id}{'*' if c.critical else ' '} {c.name}")
        if not c.passed:
            for d in c.details:
                typer.echo(f"        - {d}")
    typer.echo(f"\n{'✓ Gate APROBADO' if report.ok else '✗ Gate FALLIDO: corregir los ítems críticos (*) y volver a validar'}")
    raise typer.Exit(0 if report.ok else 1)


@app.command(rich_help_panel="Núcleo (agentes y automatización)")
def render(model: Path = typer.Option(..., "--model"), frames: Path = typer.Option(..., "--frames"),
           suite: Path = typer.Option(..., "--suite"), out: Optional[Path] = typer.Option(None, "-o", "--out"),
           date: Optional[str] = typer.Option(None, help="YYYY-MM-DD (default: hoy)")) -> None:
    """Escribe salidas/suite_<ID>_<fecha>.md (incluye la auto-revisión calculada)."""
    from .render import render_suite
    from .validate import validate as run

    m = _load_model(model)
    fs = FrameSet.model_validate_json(frames.read_text(encoding="utf-8"))
    sd = SuiteDraft.model_validate_json(suite.read_text(encoding="utf-8"))
    report = run(fs, sd)
    out = out or Path("salidas") / f"suite_{fs.story_id}_{date or dt.date.today().isoformat()}.md"
    _write(out, render_suite(fs, m, sd, report))
    typer.echo(f"{'✓' if report.ok else '✗ (gate fallido)'} {out}")
    raise typer.Exit(0 if report.ok else 1)


@app.command(rich_help_panel="Núcleo (agentes y automatización)")
def export(frames: Path = typer.Option(..., "--frames"), suite: Path = typer.Option(..., "--suite"),
           out: Path = typer.Option(Path("salidas/tests"), "-o", "--out"),
           fmt: str = typer.Option("all", "--format", help="gherkin | playwright | all")) -> None:
    """Exporta la suite a tests concretos: .feature (Gherkin en español) y steps de Playwright (playwright-bdd)."""
    from . import export as ex

    fs = FrameSet.model_validate_json(frames.read_text(encoding="utf-8"))
    sd = SuiteDraft.model_validate_json(suite.read_text(encoding="utf-8"))
    feature = ex.to_gherkin(fs, sd)
    if fmt in ("gherkin", "all"):
        _write(out / "features" / f"{fs.story_id}.feature", feature)
        typer.echo(f"✓ {out / 'features' / (fs.story_id + '.feature')}")
    if fmt in ("playwright", "all"):
        _write(out / "steps" / f"{fs.story_id}.steps.ts", ex.to_playwright_steps(feature))
        typer.echo(f"✓ {out / 'steps' / (fs.story_id + '.steps.ts')}  (implementar los TODO con Playwright)")


@app.command(rich_help_panel="Núcleo (agentes y automatización)")
def brief(frames: Path = typer.Option(..., "--frames"), hu: Path = typer.Option(..., "--hu"),
          suite: Optional[Path] = typer.Option(None, "--suite", help="Redacción existente: solo se piden los casos faltantes"),
          out: Path = typer.Option(..., "-o", "--out"), designed: bool = typer.Option(False, "--disenados",
                                                                                     help="Solo el diseño, legible")) -> None:
    """Paquete para redactar los casos con CUALQUIER IA (o, con --disenados, el diseño legible sin redactar)."""
    from . import export as ex

    fs = FrameSet.model_validate_json(frames.read_text(encoding="utf-8"))
    sd = SuiteDraft.model_validate_json(suite.read_text(encoding="utf-8")) if suite and suite.exists() else None
    body = ex.frames_markdown(fs) if designed else ex.drafting_brief(hu.read_text(encoding="utf-8"), fs, sd)
    _write(out, body)
    typer.echo(f"✓ {out}" + ("" if designed else "  → pegalo en tu IA y traé la respuesta con `tbg import-suite`"))


@app.command("import-suite", rich_help_panel="Núcleo (agentes y automatización)")
def import_suite(respuesta: Path, frames: Path = typer.Option(..., "--frames"),
                 suite: Path = typer.Option(..., "--suite", help="suite.json a crear o completar")) -> None:
    """Incorpora la redacción que devolvió otra IA (texto o JSON) y corre el gate de calidad."""
    from . import export as ex
    from .validate import validate as run

    fs = FrameSet.model_validate_json(frames.read_text(encoding="utf-8"))
    existing = SuiteDraft.model_validate_json(suite.read_text(encoding="utf-8")) if suite.exists() else None
    try:
        sd, notes = ex.import_drafts(respuesta.read_text(encoding="utf-8"), fs, existing)
    except ValueError as e:
        typer.echo(f"✗ {e}", err=True)
        raise typer.Exit(1)
    _write(suite, sd.model_dump_json(indent=2) + "\n")
    for n in notes:
        typer.echo(f"  {n}")
    report = run(fs, sd)
    typer.echo("✓ Gate APROBADO" if report.ok else "✗ Gate FALLIDO: corré `tbg validate` para ver el detalle")
    raise typer.Exit(0 if report.ok else 1)


@app.command("bug-check", rich_help_panel="Núcleo (agentes y automatización)")
def bug_check(facts: Path, report: Path = typer.Option(..., "--report"),
              out: Optional[Path] = typer.Option(None, "-o", "--out", help="Escribe el bug normalizado (markdown)"),
              as_json: bool = typer.Option(False, "--json")) -> None:
    """Verifica las citas de los hechos extraídos, detecta faltantes y clasifica severidad/prioridad por reglas."""
    from . import bug
    from .render import render_bug
    from .schemas import BugFacts

    try:
        b = BugFacts.model_validate_json(facts.read_text(encoding="utf-8"))
    except ValidationError as e:
        typer.echo(f"✗ {facts} no cumple el schema bug-facts:\n{e}", err=True)
        raise typer.Exit(2)
    text = report.read_text(encoding="utf-8")
    bc = bug.check(b, text)
    if as_json:
        _out({"title": bc.title, "ok": bc.ok, "rejected": [r.__dict__ for r in bc.rejected], "hedged": bc.hedged,
              "missing": bc.missing, "features": bc.features, "severity": bc.severity.__dict__,
              "priority": bc.priority.__dict__})
    else:
        typer.echo(bc.title)
        sev, pri = bc.severity, bc.priority
        typer.echo(f"  Severidad {sev.value}{'' if sev.firm else ' (preliminar; posibles ' + '/'.join(sev.possible) + ')'} — {sev.reason}")
        for k, v in sev.conditions.items():
            typer.echo(f"      condicionada a {k} → {v}")
        typer.echo(f"  Prioridad {pri.value}{'' if pri.firm else ' (preliminar; posibles ' + '/'.join(pri.possible) + ')'} — {pri.reason}")
        typer.echo(f"  Faltantes: {', '.join(m['label'] for m in bc.missing) or 'ninguno'}")
        for cid, name, critical, ok, details in bc.checks:
            typer.echo(f"  {'✓' if ok else '✗'} {cid}{'*' if critical else ' '} {name}")
            if not ok:
                for d in details:
                    typer.echo(f"        - {d}")
    if out:
        _write(out, render_bug(bc, text))
        typer.echo(f"→ {out}")
    raise typer.Exit(0 if bc.ok else 1)


def main() -> None:  # pragma: no cover
    app()


if __name__ == "__main__":  # pragma: no cover
    app()
