"""Asistente guiado de terminal: `tbg asistente [archivo] [--bug]`.

Lleva paso a paso por el mismo flujo que la app web (interpretación → datos y variantes → preguntas al PO →
casos → redacción → export) y escribe en work/<ID>/, así se puede continuar en `tbg ui` o con el CLI.
"""

from __future__ import annotations

from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm as _Confirm
from rich.prompt import IntPrompt, InvalidResponse, Prompt
from rich.table import Table

from . import bug, flows, llm, po, workspace

console = Console(highlight=False)


class Confirm(_Confirm):
    """Sí/no en castellano (rich espera y/n)."""

    choices = ["s", "n"]
    validate_error_message = "[prompt.invalid]Respondé s (sí) o n (no)"

    def process_response(self, value: str) -> bool:
        v = value.strip().lower()
        if v in ("s", "si", "sí", "y", "yes"):
            return True
        if v in ("n", "no"):
            return False
        raise InvalidResponse(self.validate_error_message)

    def render_default(self, default) -> str:  # muestra (s) / (n) en vez de (y) / (n)
        from rich.text import Text
        return Text(f"({'s' if default else 'n'})", style="prompt.default")


Prompt.illegal_choice_message = "[prompt.invalid.choice]Elegí una de las opciones"
IntPrompt.validate_error_message = "[prompt.invalid]Ingresá el número de la opción"
END = "FIN"


def _read_text(path: Path | None, what: str) -> str:
    if path:
        return path.read_text(encoding="utf-8")
    console.print(f"Pegá {what} y terminá con una línea que diga [bold]{END}[/bold]:")
    lines = []
    while True:
        try:
            line = input()
        except EOFError:
            break
        if line.strip() == END:
            break
        lines.append(line)
    return "\n".join(lines)


def _rel(p) -> str:
    """Ruta relativa a donde se corrió el comando (más legible), o absoluta si no se puede."""
    try:
        return str(Path(p).resolve().relative_to(Path.cwd().resolve()))
    except ValueError:
        return str(p)


def _step(n: int, title: str) -> None:
    console.print()
    console.rule(f"[bold magenta]{n} · {title}")


def _ai_label() -> str:
    try:
        return llm.config().label if llm.available() else "sin IA (se puede seguir igual)"
    except llm.LLMError as e:
        return f"configuración inválida: {e}"


# ---------------------------------------------------------------------------- HU


def run_hu(path: Path | None, out_root: Path) -> str:
    console.print(Panel.fit("Casos de prueba desde una historia de usuario\n"
                            f"IA: {_ai_label()}   ·   todo queda en work/<ID>/ (lo podés seguir con `tbg ui`)",
                            title="tbg asistente", border_style="magenta"))
    sid, warns = flows.create_hu(_read_text(path, "la historia de usuario (cualquier formato)"))
    for w in warns:
        console.print(f"[yellow]! {w}[/yellow]")

    # 1. Interpretación
    while True:
        _step(1, "Cómo se interpretó la historia")
        story = workspace.HUSpace(sid).story()
        console.print(f"[bold]{story.id}[/bold] — {story.title}")
        console.print(f"[bold]Como[/bold] {story.role or '—'}\n[bold]quiero[/bold] {story.want or '—'}\n"
                      f"[bold]para[/bold] {story.so_that or '—'}")
        for ac, text in story.acceptance_criteria:
            console.print(f"  [bold]{ac}[/bold] {text}")
        if not story.acceptance_criteria:
            console.print("[red]No se encontraron criterios de aceptación.[/red]")
        if Confirm.ask("¿Está bien interpretada?", default=bool(story.acceptance_criteria)):
            break
        import typer

        edited = typer.edit(workspace.HUSpace(sid).hu_path.read_text(encoding="utf-8"), extension=".md")
        if edited:
            workspace.HUSpace(sid).save_hu(edited)

    # 2. Datos y variantes
    _step(2, "Qué datos y variantes tiene")
    used_ai = False
    if llm.available() and Confirm.ask("¿Analizarla con IA? (3 lecturas independientes; puede tardar 1-2 minutos)",
                                       default=True):
        with console.status("Leyendo la historia…"):
            try:
                flows.analyze_with_ai(sid)
                used_ai = True
            except llm.LLMError as e:
                console.print(f"[red]La IA falló: {e}[/red]  → sigo sin IA.")
    if not used_ai:
        try:
            flows.basic_model(sid)
        except ValueError as e:
            console.print(f"[red]{e}[/red]")
            raise SystemExit(1)
        console.print("Sin IA: se usan los criterios y las reglas del equipo (sin combinaciones ni valores límite).")
    model = workspace.HUSpace(sid).model()
    if model.parameters:
        t = Table("Dato", "Criterios", "Variantes")
        for p in model.parameters:
            t.add_row(p.description, ", ".join(p.ac_refs),
                      ", ".join(f"[green]{c.description}[/green]" if c.kind == "valid" else f"[red]{c.description}[/red]"
                                for c in p.choices))
        console.print(t)
    for i, _, text in flows.pending_minorities(sid):
        if Confirm.ask(f"Lo vio una sola lectura: {text}. ¿Agregarlo?", default=False):
            try:
                flows.add_minority(sid, i)
            except ValueError as e:
                console.print(f"[yellow]{e}[/yellow]")

    # 3. Preguntas al PO
    _step(3, "Preguntas para el PO")
    model, gaps = flows.questions(sid)
    asked = [g for g in gaps if g.asked]
    form = workspace.HUSpace(sid).dir / "po.yaml"
    from .po import bounded_params, build_form

    form.write_text(build_form(model, gaps), encoding="utf-8")
    space = workspace.HUSpace(sid)
    console.print(f"{len(asked)} preguntas. Formulario para mandarle al PO: [bold]{_rel(form)}[/bold]")
    console.print(f"[dim](cuando vuelva: tbg po-apply {_rel(form)} {_rel(space.model_path)} --hu {_rel(space.hu_path)})[/dim]")
    if asked and Confirm.ask("¿Las respondés ahora? (lo que no respondas queda como [SUPUESTO])", default=True):
        answers = []
        for n, g in enumerate(asked, 1):
            console.print(f"\n[bold]P-{n}. {g.question}[/bold]\n[dim]Por qué importa: {g.why}\nDefault: {g.default}[/dim]")
            item = {"id": g.id}
            limits = {}
            for pname in bounded_params(g, model):
                desc = next(p.description for p in model.parameters if p.name == pname)
                lo = Prompt.ask(f"  Mínimo de «{desc}» (Enter = sin definir)", default="", show_default=False)
                hi = Prompt.ask(f"  Máximo de «{desc}» (Enter = sin definir)", default="", show_default=False)
                if lo or hi:
                    limits[pname] = {"min": _num(lo), "max": _num(hi), "unidad": "chars"}
            if limits:
                item["limites"] = limits
            ans = Prompt.ask("  Respuesta (Enter = queda como supuesto · d = acepto el default)", default="", show_default=False)
            if ans.strip().lower() == "d":
                item["acepto_default"] = True
            elif ans.strip():
                item["respuesta"] = ans.strip()
            answers.append(item)
        try:
            res = flows.apply_answers(sid, {"preguntas": answers})
            console.print(f"[green]✓ {po.summary(res)}[/green]")
        except ValueError as e:
            console.print(f"[red]{e}[/red]")

    # 4. Casos
    _step(4, "Casos de prueba")
    fs = flows.design(sid)
    c = fs.coverage
    console.print(f"{len(fs.frames)} casos · criterios cubiertos {c.ac_percent:g}% · pares {c.pairs_covered}/{c.pairs_total} · "
                  f"valores límite {c.boundaries_covered}/{c.boundaries_total}")
    t = Table("Caso", "Tipo", "Prioridad", "Criterios", "Qué probar", "")
    for f in fs.frames:
        flags = " ".join(x for x, on in (("humo", f.smoke), ("supuesto", bool(f.supuestos)), ("explor.", f.exploratory)) if on)
        t.add_row(f.case_id, f.type, f.priority, ", ".join(f.ac_refs) or "—", f.title_hint, flags)
    console.print(t)

    # 5. Redacción
    _step(5, "Redacción de los pasos")
    options = ["Paquete para redactar con otra IA (ChatGPT, Gemini, Claude…)", "Más tarde (en `tbg ui` o a mano)"]
    if llm.available():
        options.insert(0, f"Con la IA configurada ({_ai_label()}; puede tardar varios minutos)")
    for i, o in enumerate(options, 1):
        console.print(f"  {i}) {o}")
    choice = options[IntPrompt.ask("Opción", choices=[str(i) for i in range(1, len(options) + 1)], default=1) - 1]
    out_dir = out_root / sid
    if choice.startswith("Con la IA"):
        with console.status("Redactando y validando…"):
            try:
                report = flows.draft_with_ai(sid)
                console.print("[green]✓ Redactados. Control de calidad OK[/green]" if report.ok
                              else "[yellow]Redactados con observaciones del control de calidad (revisalas en `tbg ui`).[/yellow]")
            except llm.LLMError as e:
                console.print(f"[red]La IA falló: {e}[/red]")
    elif choice.startswith("Paquete"):
        out_dir.mkdir(parents=True, exist_ok=True)
        pkg = out_dir / f"{sid}_para_redactar.md"
        pkg.write_text(flows.brief(sid), encoding="utf-8")
        console.print(f"Paquete en [bold]{_rel(pkg)}[/bold]: pegalo en tu IA y guardá la respuesta en un archivo.")
        answer = Prompt.ask("Ruta del archivo con la respuesta (Enter = después, con `tbg import-suite` o en la app)",
                            default="", show_default=False)
        if answer.strip():
            try:
                report, notes = flows.import_answer(sid, Path(answer.strip().strip('"')).read_text(encoding="utf-8"))
                for n_ in notes:
                    console.print(f"  {n_}")
                console.print("[green]✓ Control de calidad OK[/green]" if report.ok
                              else "[yellow]El control de calidad marcó problemas: revisalos en `tbg ui`.[/yellow]")
            except (OSError, ValueError) as e:
                console.print(f"[red]{e}[/red]")

    # 6. Export
    _step(6, "Resultados")
    for p in flows.export_all(sid, out_dir):
        console.print(f"  ✓ {_rel(p)}")
    console.print(f"\nSeguí en la app con [bold]tbg ui[/bold] (la HU aparece como {sid}).")
    return sid


def _num(s: str):
    s = s.strip()
    if not s:
        return None
    return int(s) if s.lstrip("-").isdigit() else float(s)


# ---------------------------------------------------------------------------- bugs


def run_bug(path: Path | None, out_root: Path) -> str:
    console.print(Panel.fit(f"Normalizar un reporte de bug\nIA: {_ai_label()}", title="tbg asistente", border_style="magenta"))
    bid = flows.create_bug(_read_text(path, "el mensaje tal cual llegó (chat, mail, audio transcripto)"))
    out_dir = out_root / bid
    bc = None
    if llm.available() and Confirm.ask("¿Analizarlo con IA?", default=True):
        with console.status("Extrayendo hechos con cita…"):
            try:
                bc = flows.analyze_bug_with_ai(bid)
            except llm.LLMError as e:
                console.print(f"[red]La IA falló: {e}[/red]")
    if bc is None:
        out_dir.mkdir(parents=True, exist_ok=True)
        pkg = out_dir / f"{bid}_para_extraer.md"
        pkg.write_text(flows.bug_brief(bid), encoding="utf-8")
        console.print(f"Paquete para otra IA en [bold]{_rel(pkg)}[/bold]: pegalo en tu IA y guardá la respuesta (JSON).")
        answer = Prompt.ask("Ruta del archivo con la respuesta (Enter = después)", default="", show_default=False)
        if not answer.strip():
            console.print(f"Quedó en work/{bid}/. Seguí en `tbg ui`.")
            return bid
        try:
            bc = flows.import_bug_facts(bid, Path(answer.strip().strip('"')).read_text(encoding="utf-8"))
        except (OSError, ValueError) as e:
            console.print(f"[red]{e}[/red]")
            return bid

    sev, pri = bc.severity, bc.priority
    console.print(Panel(f"[bold]{bc.title}[/bold]\n\nSeveridad {sev.value}{'' if sev.firm else ' (preliminar)'} — {sev.reason}\n"
                        + "".join(f"  puede cambiar: {bug.LABELS.get(k, k)} → {v}\n" for k, v in sev.conditions.items())
                        + f"Prioridad {pri.value}{'' if pri.firm else ' (preliminar)'} — {pri.reason}",
                        border_style="red" if sev.value in ("S1", "S2") else "yellow"))
    if bc.rejected:
        console.print("[red]Datos rechazados por no tener cita en el reporte:[/red]")
        for r in bc.rejected:
            console.print(f"  - {r.path}: «{r.quote}»")
    console.print("[bold]Preguntas para quien reportó:[/bold]")
    for m in bc.missing:
        console.print(f"  {'[red]falta[/red]' if m['critical'] else '[yellow]confirmar[/yellow]'} {m['label']}: {m['question']}")
    from .render import render_bug

    out_dir.mkdir(parents=True, exist_ok=True)
    md = out_dir / f"bug_normalizado_{bid}.md"
    md.write_text(render_bug(bc, workspace.BugSpace(bid).report()), encoding="utf-8")
    console.print(f"\n  ✓ {_rel(md)}")
    return bid


def run(path: Path | None, is_bug: bool | None, out_root: Path) -> str:
    if is_bug is None:
        console.print("¿Qué querés hacer?\n  1) Casos de prueba desde una historia de usuario\n  2) Normalizar un reporte de bug")
        is_bug = IntPrompt.ask("Opción", choices=["1", "2"], default=1) == 2
    return run_bug(path, out_root) if is_bug else run_hu(path, out_root)
