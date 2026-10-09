"""Importa la salida cruda del modelo generador (prompts/generar-dataset.md) a eval/dataset/.

Uso: python eval/import_dataset.py eval/dataset/raw/lote-01.txt [--force]
Separa por líneas `=== FILE: <ruta> ===`, valida cada YAML y no pisa archivos existentes salvo --force.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "eval" / "dataset"
_ALLOWED = re.compile(r"^(hu/HU-[\w-]+\.md|bugs/BUG-[\w-]+\.md|golden/(hu|bug)-[\w-]+\.(gaps\.)?yaml)$")


def main(raw_path: str, force: bool = False) -> None:
    raw = Path(raw_path).read_text(encoding="utf-8")
    parts = re.split(r"^=== FILE: (.+?) ===\s*$", raw, flags=re.M)
    written, errors = [], []
    for rel, body in zip(parts[1::2], parts[2::2]):
        rel = rel.strip()
        body = body.strip().removeprefix("```").removesuffix("```").strip() + "\n"
        if not _ALLOWED.match(rel):
            errors.append(f"ruta no permitida: {rel}")
            continue
        if rel.endswith(".yaml"):
            try:
                data = yaml.safe_load(body)
            except yaml.YAMLError as e:
                errors.append(f"{rel}: YAML inválido ({e.__class__.__name__})")
                continue
            if rel.startswith("golden/hu-") and data:
                data.setdefault("hu_file", f"eval/dataset/hu/{data['story']}.md")
                body = yaml.safe_dump(data, allow_unicode=True, sort_keys=False)
        dest = DATASET / rel
        if dest.exists() and not force:
            errors.append(f"{rel}: ya existe (usar --force)")
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(body, encoding="utf-8")
        written.append(rel)
    print(f"✓ {len(written)} archivos importados en {DATASET.relative_to(ROOT)}")
    for e in errors:
        print(f"  ✗ {e}")


if __name__ == "__main__":
    main(sys.argv[1], force="--force" in sys.argv)
