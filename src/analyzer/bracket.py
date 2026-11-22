"""Suelo determinista del bracket de Commander (ver prompts/knowledge/brackets.md).

Todo lo que se puede decidir de forma objetiva (Game Changers presentes,
candidatas a destrucción masiva de tierras, cartas de turno extra,
combos verificados contra Commander Spellbook) se calcula aquí. Claude
confirma y explica estas señales, pero no las recalcula ni las adivina
de memoria — el principio de siempre.
"""

from __future__ import annotations

import json
import re
import sqlite3
from pathlib import Path

from analyzer import cards as cards_module
from analyzer.cards import Card

GAME_CHANGERS_PATH = Path(__file__).resolve().parents[2] / "data" / "game_changers.json"

_MASS_LAND_DESTRUCTION_PATTERNS = [
    re.compile(r"destroy all lands", re.IGNORECASE),
    re.compile(r"destroy each land", re.IGNORECASE),
    re.compile(r"lands? don't untap", re.IGNORECASE),
    re.compile(r"each player sacrifices \w+ lands?", re.IGNORECASE),
]
_EXTRA_TURN_PATTERN = re.compile(r"\bextra turns?\b", re.IGNORECASE)


def load_game_changers() -> frozenset[str]:
    """Nombres normalizados (minúsculas) de la lista oficial de Game Changers."""
    data = json.loads(GAME_CHANGERS_PATH.read_text(encoding="utf-8"))
    return frozenset(name.strip().lower() for name in data["cards"])


def find_game_changers(
    commanders: list[Card], deck_cards: list[Card], game_changers: frozenset[str] | None = None
) -> list[str]:
    """Game Changers presentes en el deck (comandante incluido), sin duplicados."""
    gc = game_changers if game_changers is not None else load_game_changers()
    seen: dict[str, str] = {}
    for card in [*commanders, *deck_cards]:
        normalized = card.name.strip().lower()
        if normalized in gc and normalized not in seen:
            seen[normalized] = card.name
    return list(seen.values())


def find_mass_land_destruction_candidates(deck_cards: list[Card]) -> list[str]:
    """Candidatas a destrucción masiva de tierras, por patrones de texto.
    Son candidatas, no confirmadas: Claude decide si de verdad cuentan
    (p. ej. Field of the Dead no es destrucción de tierras)."""
    seen: dict[str, str] = {}
    for card in deck_cards:
        text = card.oracle_text or ""
        if any(p.search(text) for p in _MASS_LAND_DESTRUCTION_PATTERNS):
            seen.setdefault(card.name.strip().lower(), card.name)
    return list(seen.values())


def find_extra_turn_cards(deck_cards: list[Card]) -> list[str]:
    """Cartas cuyo texto oracle menciona tomar un turno extra."""
    seen: dict[str, str] = {}
    for card in deck_cards:
        if _EXTRA_TURN_PATTERN.search(card.oracle_text or ""):
            seen.setdefault(card.name.strip().lower(), card.name)
    return list(seen.values())


def classify_combo_speed(conn: sqlite3.Connection, combo: dict) -> str:
    """'temprano' si el coste de maná combinado de las piezas es bajo
    (≤4), 'tardío' si no. Heurística propia a partir del CMC local, no
    algo que etiquete Commander Spellbook directamente: es una
    aproximación a "montable antes del turno 6 con piezas baratas", no
    una certeza (ver sección 4.3 de brackets.md)."""
    total_cmc = 0.0
    for name in combo["cartas"]:
        card = cards_module.get_card_by_name(conn, name)
        if card is not None:
            total_cmc += card.cmc
    return "temprano" if total_cmc <= 4 else "tardío"


def compute_floor(
    commanders: list[Card],
    deck_cards: list[Card],
    conn: sqlite3.Connection | None = None,
    combos: list[dict] | None = None,
) -> dict:
    """Calcula el suelo de bracket y las señales duras que lo justifican.

    Devuelve un dict con ``floor`` (1-4) y listas de cartas detectadas, para
    pasárselo a Claude como dato ya resuelto (ver sección 5 de
    ``prompts/knowledge/brackets.md``). ``combos`` (de
    ``analyzer.combos.find_combos``) es opcional: sin ``conn`` no se
    puede clasificar su velocidad, así que ese dato ya resuelto se omite
    sin más (no se recalcula aquí).
    """
    game_changers = find_game_changers(commanders, deck_cards)
    mld_candidates = find_mass_land_destruction_candidates(deck_cards)
    extra_turn_cards = find_extra_turn_cards(deck_cards)
    combo_info = []
    if combos and conn is not None:
        combo_info = [{**combo, "velocidad": classify_combo_speed(conn, combo)} for combo in combos]

    floor = 1
    reasons: list[str] = []

    if len(game_changers) >= 4:
        floor = max(floor, 4)
        reasons.append(f"{len(game_changers)} Game Changers → mínimo bracket 4")
    elif len(game_changers) >= 1:
        floor = max(floor, 3)
        reasons.append(f"{len(game_changers)} Game Changer(s) → mínimo bracket 3")

    if mld_candidates:
        floor = max(floor, 4)
        reasons.append("Candidatas a destrucción masiva de tierras → mínimo bracket 4")

    if len(extra_turn_cards) >= 2:
        floor = max(floor, 4)
        reasons.append("Varias cartas de turno extra (posible cadena) → mínimo bracket 4")
    elif len(extra_turn_cards) == 1:
        floor = max(floor, 2)
        reasons.append("Una carta de turno extra suelta → mínimo bracket 2")

    if any(c["velocidad"] == "temprano" for c in combo_info):
        floor = max(floor, 4)
        reasons.append("Combo de 2+ piezas montable pronto (coste bajo) → mínimo bracket 4")
    elif combo_info:
        floor = max(floor, 3)
        reasons.append("Combo de 2+ piezas solo viable tarde → mínimo bracket 3")

    return {
        "floor": floor,
        "razones_suelo": reasons,
        "game_changers": game_changers,
        "destruccion_tierras_candidatas": mld_candidates,
        "cartas_turno_extra": extra_turn_cards,
        "combos": combo_info,
    }
