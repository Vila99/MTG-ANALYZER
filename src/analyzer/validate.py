"""Valida las sugerencias de Claude contra la base de datos de cartas.

Toda carta que sugiera Claude (corte o añadido) se valida antes de
mostrarla al usuario: que exista en Scryfall, que sea legal en el formato,
que encaje en la identidad de color del comandante y, para los añadidos,
que no esté ya en el deck (salvo tierras básicas, que no son singleton).
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


def validate_cut(suggested_name: str, deck_card_names: set[str]) -> ValidationResult:
    """Un corte sugerido solo es válido si la carta está de verdad en el deck."""
    if suggested_name not in deck_card_names:
        return ValidationResult(False, "la carta no está en el deck")
    return ValidationResult(True)


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
    """Devuelve una copia del análisis de Claude con ``cortes_sugeridos`` y
    ``anadidos_sugeridos`` filtrados a solo las sugerencias que pasan la
    validación."""
    commander_identity: set[str] = set()
    for commander in commanders:
        commander_identity |= set(commander.color_identity)
    deck_card_names = {card.name for card in deck_cards}

    validated_cuts = [
        cut
        for cut in analysis.get("cortes_sugeridos", [])
        if validate_cut(cut["carta"], deck_card_names).valido
    ]
    validated_additions = [
        addition
        for addition in analysis.get("anadidos_sugeridos", [])
        if validate_addition(
            conn, addition["carta"], commander_identity, deck_card_names
        ).valido
    ]

    return {
        **analysis,
        "cortes_sugeridos": validated_cuts,
        "anadidos_sugeridos": validated_additions,
    }
