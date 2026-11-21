"""Punto de entrada: ``analyze deck.txt``."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

from analyzer import cards as cards_module
from analyzer import report
from analyzer import roles as roles_module
from analyzer import rubric
from analyzer.cards import Card
from analyzer.parser import ParsedDeck, parse_decklist


def _resolve_cards(
    conn: sqlite3.Connection, parsed: ParsedDeck
) -> tuple[list[Card], list[Card], list[str]]:
    commanders: list[Card] = []
    deck_cards: list[Card] = []
    missing: list[str] = []

    for name in parsed.commanders:
        card = cards_module.get_card_by_name(conn, name)
        if card is None:
            missing.append(name)
        else:
            commanders.append(card)

    for entry in parsed.cards:
        card = cards_module.get_card_by_name(conn, entry.name)
        if card is None:
            missing.append(entry.name)
        else:
            deck_cards.extend([card] * entry.quantity)

    return commanders, deck_cards, missing


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
    args = parser.parse_args(argv)

    if not args.deck_file.exists():
        print(f"No se encontró el archivo del deck: {args.deck_file}", file=sys.stderr)
        return 1

    if not args.db.exists():
        print(f"No se encontró la base de datos de cartas en {args.db}.", file=sys.stderr)
        print("Ejecuta `python scripts/load_scryfall.py` antes de analizar un deck.", file=sys.stderr)
        return 1

    text = args.deck_file.read_text(encoding="utf-8")
    parsed = parse_decklist(text)

    conn = cards_module.connect(args.db)
    try:
        commanders, deck_cards, missing = _resolve_cards(conn, parsed)
        role_counts = roles_module.count_roles(conn, deck_cards)
    finally:
        conn.close()

    rubric_status = rubric.evaluate_role_counts(role_counts)

    if args.json:
        print(
            json.dumps(
                _build_json_summary(commanders, deck_cards, missing, role_counts, rubric_status),
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        print(report.render(commanders, deck_cards, missing, role_counts, rubric_status))

    return 2 if missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
