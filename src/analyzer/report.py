"""Formatea los resultados del análisis como texto para la terminal."""

from __future__ import annotations

from analyzer.cards import Card
from analyzer import metrics

_COLOR_NAMES = {"W": "Blanco", "U": "Azul", "B": "Negro", "R": "Rojo", "G": "Verde"}
_ROLE_NAMES = {
    "land": "Tierras",
    "ramp": "Ramp",
    "draw": "Robo de cartas",
    "removal": "Removal puntual",
    "wipe": "Wipes",
    "protection": "Protección",
    "tutor": "Tutores",
    "wincon": "Condiciones de victoria",
    "synergy": "Sinergia",
    "other": "Sin clasificar",
}
_RUBRIC_STATUS_LABEL = {"bajo": "bajo", "ok": "dentro de rango", "alto": "alto"}


def render(
    commanders: list[Card],
    deck_cards: list[Card],
    missing: list[str],
    role_counts: dict[str, int] | None = None,
    rubric_status: dict[str, str] | None = None,
) -> str:
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

    if role_counts is not None:
        lines.append("")
        lines.append("=== Roles (por reglas; 'sin clasificar' puede necesitar revisión con Haiku) ===")
        for role in ("ramp", "draw", "removal", "wipe", "tutor", "protection", "synergy", "wincon", "other"):
            count = role_counts.get(role, 0)
            if count:
                lines.append(f"  {_ROLE_NAMES[role]}: {count}")

    if rubric_status is not None:
        lines.append("")
        lines.append("=== Comparación con el rubric base ===")
        for role, status in rubric_status.items():
            count = role_counts.get(role, 0) if role_counts else 0
            lines.append(f"  {_ROLE_NAMES[role]}: {count} ({_RUBRIC_STATUS_LABEL[status]})")

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
