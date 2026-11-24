"""Compara dos resultados guardados por run_eval.py, para ver qué cambió
entre dos versiones del prompt/rubric (Fase 5 de CLAUDE.md).

Uso:
    python scripts/compare_eval.py data/eval_runs/jasnah/2026-01-01T00-00-00.json data/eval_runs/jasnah/2026-02-01T00-00-00.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def _names(items: list[dict], key: str) -> set[str]:
    return {item[key] for item in items}


def compare(old: dict, new: dict) -> str:
    lines: list[str] = []
    lines.append(f"Deck: {old.get('deck', '?')}")
    lines.append(f"Antes: {old.get('timestamp', '?')}  |  Después: {new.get('timestamp', '?')}")

    old_analysis = old["validated_analysis"]
    new_analysis = new["validated_analysis"]
    diffs: list[str] = []

    if old_analysis.get("estrategia_detectada") != new_analysis.get("estrategia_detectada"):
        diffs.append(
            f"Estrategia: '{old_analysis.get('estrategia_detectada')}' -> "
            f"'{new_analysis.get('estrategia_detectada')}'"
        )
    if old_analysis.get("arquetipo") != new_analysis.get("arquetipo"):
        diffs.append(f"Arquetipo: '{old_analysis.get('arquetipo')}' -> '{new_analysis.get('arquetipo')}'")

    old_candidates = {
        candidata["carta"]
        for problema in old_analysis.get("problemas", [])
        for candidata in problema.get("candidatas_sugeridas", [])
    }
    new_candidates = {
        candidata["carta"]
        for problema in new_analysis.get("problemas", [])
        for candidata in problema.get("candidatas_sugeridas", [])
    }
    if new_candidates - old_candidates:
        diffs.append(f"Candidatas nuevas: {sorted(new_candidates - old_candidates)}")
    if old_candidates - new_candidates:
        diffs.append(f"Candidatas que ya no se sugieren: {sorted(old_candidates - new_candidates)}")

    old_problem_categories = _names(old_analysis.get("problemas", []), "categoria")
    new_problem_categories = _names(new_analysis.get("problemas", []), "categoria")
    if old_problem_categories != new_problem_categories:
        diffs.append(
            f"Categorías de problemas: {sorted(old_problem_categories)} -> "
            f"{sorted(new_problem_categories)}"
        )

    lines.append("")
    lines.extend(diffs if diffs else ["Sin diferencias relevantes en el análisis validado."])
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="compare_eval", description="Compara dos resultados guardados por run_eval.py"
    )
    parser.add_argument("old", type=Path)
    parser.add_argument("new", type=Path)
    args = parser.parse_args(argv)

    old = json.loads(args.old.read_text(encoding="utf-8"))
    new = json.loads(args.new.read_text(encoding="utf-8"))

    print(compare(old, new))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
