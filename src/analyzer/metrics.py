"""Métricas objetivas de un deck: curva de maná, tierras, pips, identidad de color, legalidad.

Todas las funciones son puras (reciben datos, devuelven datos) para que sean
fáciles de testear sin base de datos ni red.
"""

from __future__ import annotations

import re
from collections import Counter
from collections.abc import Iterable

from analyzer.cards import Card

_COLORS = ("W", "U", "B", "R", "G")
_MANA_SYMBOL_RE = re.compile(r"\{([^}]+)\}")


def nonland_cards(cards: Iterable[Card]) -> list[Card]:
    return [c for c in cards if not c.is_land]


def mana_curve(cards: Iterable[Card]) -> dict[int, int]:
    """Distribución de CMC (solo cartas que no son tierra), agrupada por entero."""
    curve: Counter[int] = Counter()
    for card in nonland_cards(cards):
        curve[int(card.cmc)] += 1
    return dict(sorted(curve.items()))


def average_cmc(cards: Iterable[Card]) -> float:
    """CMC medio, excluyendo tierras. Devuelve 0.0 si no hay cartas no-tierra."""
    nonlands = nonland_cards(cards)
    if not nonlands:
        return 0.0
    return sum(c.cmc for c in nonlands) / len(nonlands)


def count_lands(cards: Iterable[Card]) -> int:
    return sum(1 for c in cards if c.is_land)


def deck_size(cards: Iterable[Card], commanders: Iterable[Card] = ()) -> int:
    return sum(1 for _ in cards) + sum(1 for _ in commanders)


def color_pips(cards: Iterable[Card]) -> dict[str, int]:
    """Cuenta símbolos de maná coloreados en el coste. Los símbolos híbridos
    (incl. Phyrexian) suman a cada color que contienen."""
    pips: Counter[str] = Counter({c: 0 for c in _COLORS})
    for card in cards:
        for symbol in _MANA_SYMBOL_RE.findall(card.mana_cost):
            for part in symbol.split("/"):
                if part in _COLORS:
                    pips[part] += 1
    return dict(pips)


def mana_sources(cards: Iterable[Card]) -> dict[str, int]:
    """Cuenta cuántas cartas pueden producir cada color de maná (tierras, rocas,
    criaturas de maná...) según ``produced_mana`` de Scryfall."""
    sources: Counter[str] = Counter({c: 0 for c in _COLORS})
    for card in cards:
        for color in card.produced_mana:
            if color in _COLORS:
                sources[color] += 1
    return dict(sources)


def color_identity_violations(
    cards: Iterable[Card], commander_identity: set[str]
) -> list[Card]:
    """Cartas cuya identidad de color no está contenida en la del comandante."""
    return [
        card
        for card in cards
        if not set(card.color_identity).issubset(commander_identity)
    ]


def illegal_cards(cards: Iterable[Card], format_name: str = "commander") -> list[Card]:
    """Cartas no legales en el formato indicado."""
    return [card for card in cards if not card.is_legal(format_name)]
