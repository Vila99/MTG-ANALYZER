"""Formatea los resultados del análisis como texto para la terminal."""

from __future__ import annotations

from analyzer.cards import Card
from analyzer import metrics

_COLOR_NAMES = {"W": "Blanco", "U": "Azul", "B": "Negro", "R": "Rojo", "G": "Verde"}


def render(commanders: list[Card], deck_cards: list[Card], missing: list[str]) -> str:
    lines: list[str] = []

    lines.append("=== Comandante(s) ===")
    if commanders:
        for card in commanders:
            identity = "".join(card.color_identity) or "Incoloro"
            lines.append(f"  - {card.name} ({identity})")
    else:
        lines.append("  (no se detectó comandante)")

    total = metrics.deck_size(deck_cards, commanders)
    lines.append("")
    lines.append(f"=== Tamaño del deck: {total} cartas ===")

    lands = metrics.count_lands(deck_cards)
    lines.append("")
    lines.append(f"Tierras: {lands}")

    curve = metrics.mana_curve(deck_cards)
    avg_cmc = metrics.average_cmc(deck_cards)
    lines.append("")
    lines.append(f"Curva de maná (sin tierras, CMC medio {avg_cmc:.2f}):")
    for cmc, count in curve.items():
        lines.append(f"  {cmc}: {'#' * count} ({count})")

    pips = metrics.color_pips(deck_cards)
    sources = metrics.mana_sources(deck_cards)
    lines.append("")
    lines.append("Pips vs. fuentes de maná por color:")
    for color in ("W", "U", "B", "R", "G"):
        lines.append(
            f"  {_COLOR_NAMES[color]}: {pips.get(color, 0)} pips / {sources.get(color, 0)} fuentes"
        )

    commander_identity = set()
    for card in commanders:
        commander_identity |= set(card.color_identity)
    if commander_identity:
        violations = metrics.color_identity_violations(deck_cards, commander_identity)
        if violations:
            lines.append("")
            lines.append("Fuera de la identidad de color del comandante:")
            for card in violations:
                lines.append(f"  - {card.name} ({''.join(card.color_identity)})")

    illegal = metrics.illegal_cards(deck_cards, "commander")
    if illegal:
        lines.append("")
        lines.append("No legales en Commander:")
        for card in illegal:
            lines.append(f"  - {card.name}")

    if missing:
        lines.append("")
        lines.append("No encontradas en la base de datos de cartas:")
        for name in missing:
            lines.append(f"  - {name}")

    return "\n".join(lines)
