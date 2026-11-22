"""Punto de entrada: ``analyze deck.txt``."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from analyzer import cards as cards_module
from analyzer import report
from analyzer import roles as roles_module
from analyzer import rubric
from analyzer.cards import Card
from analyzer.parser import parse_decklist


def _build_json_summary(
    commanders: list[Card],
    deck_cards: list[Card],
    missing: list[str],
    role_counts: dict[str, int],
    rubric_status: dict[str, str],
) -> dict:
    from analyzer import metrics

    return {
        "comandantes": [c.name for c in commanders],
        "tamano_deck": metrics.deck_size(deck_cards, commanders),
        "tierras": metrics.count_lands(deck_cards),
        "cmc_medio": round(metrics.average_cmc(deck_cards), 2),
        "curva_mana": metrics.mana_curve(deck_cards),
        "pips": metrics.color_pips(deck_cards),
        "fuentes_mana": metrics.mana_sources(deck_cards),
        "no_legales": [c.name for c in metrics.illegal_cards(deck_cards)],
        "no_encontradas": missing,
        "roles": role_counts,
        "rubric": rubric_status,
    }


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(
        prog="analyze", description="Analiza un deck de Magic: The Gathering (Commander/EDH)."
    )
    parser.add_argument("deck_file", type=Path, help="Ruta a la lista del deck en texto plano")
    parser.add_argument("--bracket", type=int, choices=range(1, 6), help="Nivel de poder objetivo (1-5)")
    parser.add_argument("--budget", type=float, help="Precio máximo por carta o total")
    parser.add_argument("--json", action="store_true", help="Salida en JSON en vez de texto")
    parser.add_argument(
        "--db", type=Path, default=cards_module.DEFAULT_DB_PATH, help="Ruta a data/cards.db"
    )
    parser.add_argument(
        "--ai",
        action="store_true",
        help="Pide a Claude el análisis completo del deck (requiere ANTHROPIC_API_KEY)",
    )
    parser.add_argument(
        "--style", choices=["casual", "focused", "cedh"], default="casual", help="Estilo del deck (con --ai)"
    )
    parser.add_argument(
        "--allow-combos", action="store_true", help="Permite sugerir combos (con --ai)"
    )
    parser.add_argument(
        "--avoid", action="append", default=[], help="Carta o mecánica a evitar (con --ai; se puede repetir)"
    )
    args = parser.parse_args(argv)

    if not args.deck_file.exists():
        print(f"No se encontró el archivo del deck: {args.deck_file}", file=sys.stderr)
        return 1

    if not args.db.exists():
        print(f"No se encontró la base de datos de cartas en {args.db}.", file=sys.stderr)
        print("Ejecuta `python scripts/load_scryfall.py` antes de analizar un deck.", file=sys.stderr)
        return 1

    client = None
    if args.ai:
        from analyzer import llm

        try:
            client = llm.get_client()
        except RuntimeError as exc:
            print(str(exc), file=sys.stderr)
            return 1

    text = args.deck_file.read_text(encoding="utf-8")
    parsed = parse_decklist(text)

    analysis_run = None
    conn = cards_module.connect(args.db)
    try:
        commanders, deck_cards, missing = cards_module.resolve_deck(conn, parsed)
        role_counts = roles_module.count_roles(conn, deck_cards)

        if args.ai:
            from analyzer import pipeline

            card_roles = roles_module.classify_cards(conn, deck_cards)
            params = {
                "bracket": args.bracket,
                "budget": args.budget,
                "style": args.style,
                "allow_combos": args.allow_combos,
                "avoid": args.avoid,
            }
            analysis_run = pipeline.run_analysis(
                client, conn, commanders, deck_cards, card_roles, params
            )
    finally:
        conn.close()

    rubric_status = rubric.evaluate_role_counts(role_counts)
    analysis = analysis_run.validated_analysis if analysis_run else None

    if args.json:
        summary = _build_json_summary(commanders, deck_cards, missing, role_counts, rubric_status)
        if analysis is not None:
            summary["analisis"] = analysis
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        print(report.render(commanders, deck_cards, missing, role_counts, rubric_status))
        if analysis is not None:
            print()
            print(report.render_analysis(analysis))

    return 2 if missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
