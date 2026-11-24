"""Valida las sugerencias de Claude contra la base de datos de cartas.

Toda carta candidata que sugiera Claude (``candidatas_sugeridas`` dentro de
cada ``problema``) se valida antes de mostrarla al usuario: que exista en
Scryfall, que sea legal en el formato, que encaje en la identidad de color
del comandante y que no esté ya en el deck (salvo tierras básicas, que no
son singleton).
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass

from analyzer.cards import Card, get_card_by_name

_BASIC_LAND_NAMES = {"plains", "island", "swamp", "mountain", "forest", "wastes"}


@dataclass(frozen=True)
class ValidationResult:
    valido: bool
    motivo_rechazo: str | None = None


def validate_addition(
    conn: sqlite3.Connection,
    suggested_name: str,
    commander_identity: set[str],
    deck_card_names: set[str],
    format_name: str = "commander",
) -> ValidationResult:
    card = get_card_by_name(conn, suggested_name)
    if card is None:
        return ValidationResult(False, "la carta no existe (no se encontró en Scryfall)")
    if not card.is_legal(format_name):
        return ValidationResult(False, f"no es legal en {format_name}")
    if not set(card.color_identity).issubset(commander_identity):
        return ValidationResult(False, "fuera de la identidad de color del comandante")
    is_basic_land = card.name.lower() in _BASIC_LAND_NAMES
    if not is_basic_land and card.name in deck_card_names:
        return ValidationResult(False, "ya está en el deck")
    return ValidationResult(True)


def validate_analysis(
    conn: sqlite3.Connection,
    analysis: dict,
    commanders: list[Card],
    deck_cards: list[Card],
) -> dict:
    """Devuelve una copia del análisis de Claude con las
    ``candidatas_sugeridas`` de cada ``problema`` filtradas a solo las que
    pasan la validación."""
    commander_identity: set[str] = set()
    for commander in commanders:
        commander_identity |= set(commander.color_identity)
    deck_card_names = {card.name for card in deck_cards}

    validated_problemas = [
        {
            **problema,
            "candidatas_sugeridas": [
                candidata
                for candidata in problema.get("candidatas_sugeridas", [])
                if validate_addition(
                    conn, candidata["carta"], commander_identity, deck_card_names
                ).valido
            ],
        }
        for problema in analysis.get("problemas", [])
    ]

    return {**analysis, "problemas": validated_problemas}
