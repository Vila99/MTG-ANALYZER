"""Guarda el payload y el resultado del análisis de Claude para los decks de
data/sample_decks/, para poder comparar versiones del rubric/prompt a lo
largo del tiempo (Fase 5 de CLAUDE.md).

Uso:
    python scripts/run_eval.py
    python scripts/run_eval.py --deck data/sample_decks/jasnah.txt
    python scripts/run_eval.py --bracket 3 --style focused

Requiere ANTHROPIC_API_KEY configurada: hace una llamada real a Sonnet por
cada deck evaluado.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from analyzer import cards as cards_module
from analyzer import llm
from analyzer import pipeline
from analyzer import roles as roles_module
from analyzer.parser import parse_decklist

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SAMPLE_DECKS_DIR = PROJECT_ROOT / "data" / "sample_decks"
EVAL_RUNS_DIR = PROJECT_ROOT / "data" / "eval_runs"


def _run_one(deck_path: Path, db_path: Path, client, params: dict) -> dict:
    text = deck_path.read_text(encoding="utf-8")
    parsed = parse_decklist(text)

    conn = cards_module.connect(db_path)
    try:
        commanders, deck_cards, missing = cards_module.resolve_deck(conn, parsed)
        card_roles = roles_module.classify_cards(conn, deck_cards)
        run = pipeline.run_analysis(client, conn, commanders, deck_cards, card_roles, params)
    finally:
        conn.close()

    return {
        "deck": deck_path.name,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "params": params,
        "comandantes": [c.name for c in commanders],
        "cartas_no_encontradas": missing,
        "payload": run.payload,
        "raw_analysis": run.raw_analysis,
        "validated_analysis": run.validated_analysis,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="run_eval", description="Ejecuta y guarda el análisis de Claude para decks de muestra."
    )
    parser.add_argument(
        "--deck", type=Path, action="append", help="Ruta a un deck concreto (se puede repetir); por defecto, todos los de data/sample_decks/"
    )
    parser.add_argument("--db", type=Path, default=cards_module.DEFAULT_DB_PATH)
    parser.add_argument("--bracket", type=int, choices=range(1, 6))
    parser.add_argument("--budget", type=float)
    parser.add_argument("--style", choices=["casual", "focused", "cedh"], default="casual")
    parser.add_argument("--allow-combos", action="store_true")
    parser.add_argument("--avoid", action="append", default=[])
    args = parser.parse_args(argv)

    deck_paths = args.deck or sorted(SAMPLE_DECKS_DIR.glob("*.txt"))
    if not deck_paths:
        print(f"No hay decks de muestra en {SAMPLE_DECKS_DIR}")
        return 1

    client = llm.get_client()
    params = {
        "bracket": args.bracket,
        "budget": args.budget,
        "style": args.style,
        "allow_combos": args.allow_combos,
        "avoid": args.avoid,
    }

    for deck_path in deck_paths:
        print(f"Analizando {deck_path.name}...")
        record = _run_one(deck_path, args.db, client, params)

        out_dir = EVAL_RUNS_DIR / deck_path.stem
        out_dir.mkdir(parents=True, exist_ok=True)
        timestamp_slug = record["timestamp"].replace(":", "-")
        out_path = out_dir / f"{timestamp_slug}.json"
        out_path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"  guardado en {out_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
