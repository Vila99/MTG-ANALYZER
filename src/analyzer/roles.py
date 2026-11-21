"""Clasificación de cartas por rol: reglas sobre el texto oracle, con Haiku
como respaldo (solo cuando las reglas no deciden) y caché en SQLite.

Una carta puede tener varios roles. ``classify_card`` es la función
principal: primero mira la caché, luego las reglas y, si las reglas no
encuentran nada, delega en la función de clasificación por LLM que se le
pase (ver ``analyzer.llm.classify_card_with_haiku``).
"""

from __future__ import annotations

import json
import re
import sqlite3
from collections.abc import Callable, Iterable

from analyzer.cards import Card, normalize_name

ROLES = (
    "land",
    "ramp",
    "draw",
    "removal",
    "wipe",
    "protection",
    "tutor",
    "wincon",
    "synergy",
    "other",
)

LlmClassifier = Callable[[Card], list[str]]

_RAMP_PATTERNS = [
    re.compile(r"search your library for .*land card", re.IGNORECASE),
    re.compile(r"you may play an additional land", re.IGNORECASE),
]
# Rocas/dorks de maná (ej. Sol Ring: "Add {C}{C}.", Arcane Signet: "Add one
# mana of any color..."). Solo cuentan como ramp si la carta no es una
# tierra: una tierra que simplemente añade maná (duales, triomas...) no es
# "ramp", solo produce su maná normal.
_RAMP_NONLAND_PATTERNS = [
    re.compile(r"\badd (one|two|three|x) mana\b", re.IGNORECASE),
    re.compile(r"\badd \{", re.IGNORECASE),
]
_DRAW_PATTERNS = [
    re.compile(r"draws? (?:\w+ )?cards?\b", re.IGNORECASE),
]
_PT_MODIFIER = r"-(?:\d+|x)/-(?:\d+|x)"
_WIPE_PATTERNS = [
    re.compile(r"destroy all creatures", re.IGNORECASE),
    re.compile(r"destroy each creature", re.IGNORECASE),
    re.compile(rf"each creature gets? {_PT_MODIFIER}", re.IGNORECASE),
    re.compile(rf"all creatures get {_PT_MODIFIER}", re.IGNORECASE),
    re.compile(r"deals? \d+ damage to each creature", re.IGNORECASE),
]
_REMOVAL_PATTERNS = [
    re.compile(r"destroy target (creature|permanent|artifact|enchantment|planeswalker)", re.IGNORECASE),
    re.compile(r"exile target (creature|permanent|artifact|enchantment|planeswalker)", re.IGNORECASE),
    re.compile(rf"target creature gets {_PT_MODIFIER}", re.IGNORECASE),
    re.compile(r"deals? \d+ damage to target (creature|player|any target)", re.IGNORECASE),
    re.compile(r"put target creature.*(library|graveyard)", re.IGNORECASE),
    re.compile(r"return target .*to (its|their) owner's hand", re.IGNORECASE),
]
_PROTECTION_PATTERNS = [
    re.compile(r"hexproof", re.IGNORECASE),
    re.compile(r"indestructible", re.IGNORECASE),
    re.compile(r"protection from", re.IGNORECASE),
    re.compile(r"can't be countered", re.IGNORECASE),
    re.compile(r"\bshroud\b", re.IGNORECASE),
]
_TUTOR_PATTERNS = [
    re.compile(r"search your library for a card", re.IGNORECASE),
    re.compile(
        r"search your library for an? (artifact|creature|enchantment|instant|sorcery|planeswalker)",
        re.IGNORECASE,
    ),
]


def classify_by_rules(card: Card) -> list[str]:
    """Clasifica una carta por patrones de texto. Devuelve ``[]`` si ninguna
    regla encaja (la carta queda pendiente del respaldo de Haiku)."""
    roles: list[str] = []
    if card.is_land:
        roles.append("land")

    text = card.oracle_text or ""

    if any(p.search(text) for p in _RAMP_PATTERNS):
        roles.append("ramp")
    elif not card.is_land and any(p.search(text) for p in _RAMP_NONLAND_PATTERNS):
        roles.append("ramp")
    if any(p.search(text) for p in _DRAW_PATTERNS):
        roles.append("draw")
    if any(p.search(text) for p in _WIPE_PATTERNS):
        roles.append("wipe")
    elif any(p.search(text) for p in _REMOVAL_PATTERNS):
        roles.append("removal")
    if any(p.search(text) for p in _PROTECTION_PATTERNS):
        roles.append("protection")
    if "ramp" not in roles and any(p.search(text) for p in _TUTOR_PATTERNS):
        roles.append("tutor")

    return roles


# Incrementar cada vez que cambien los patrones de classify_by_rules: invalida
# automáticamente las entradas de caché con source="rules" calculadas con
# una versión anterior de las reglas (las de source="llm" no se ven afectadas).
RULES_VERSION = 2


def ensure_role_cache_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS card_roles (
            name_normalized TEXT PRIMARY KEY,
            roles TEXT NOT NULL,
            source TEXT NOT NULL,
            rules_version INTEGER
        )
        """
    )
    columns = {row[1] for row in conn.execute("PRAGMA table_info(card_roles)")}
    if "rules_version" not in columns:
        conn.execute("ALTER TABLE card_roles ADD COLUMN rules_version INTEGER")


def get_cached_roles(conn: sqlite3.Connection, card: Card) -> list[str] | None:
    row = conn.execute(
        "SELECT roles, source, rules_version FROM card_roles WHERE name_normalized = ?",
        (normalize_name(card.name),),
    ).fetchone()
    if row is None:
        return None
    roles_json, source, rules_version = row
    if source == "rules" and rules_version != RULES_VERSION:
        return None
    return json.loads(roles_json)


def _cache_roles(conn: sqlite3.Connection, card: Card, roles: list[str], source: str) -> None:
    rules_version = RULES_VERSION if source == "rules" else None
    conn.execute(
        """
        INSERT INTO card_roles (name_normalized, roles, source, rules_version) VALUES (?, ?, ?, ?)
        ON CONFLICT(name_normalized) DO UPDATE SET
            roles=excluded.roles, source=excluded.source, rules_version=excluded.rules_version
        """,
        (normalize_name(card.name), json.dumps(roles), source, rules_version),
    )
    conn.commit()


def classify_card(
    conn: sqlite3.Connection,
    card: Card,
    llm_classify: LlmClassifier | None = None,
) -> list[str]:
    """Clasifica una carta por rol: caché -> reglas -> Haiku como respaldo.

    Si las reglas no deciden nada y no se pasa ``llm_classify``, devuelve
    ``["other"]`` sin guardarlo en caché, para que una ejecución futura con
    el respaldo de Haiku disponible pueda clasificarla de verdad.
    """
    ensure_role_cache_table(conn)

    cached = get_cached_roles(conn, card)
    if cached is not None:
        return cached

    roles = classify_by_rules(card)
    if roles:
        _cache_roles(conn, card, roles, source="rules")
        return roles

    if llm_classify is not None:
        roles = llm_classify(card) or ["other"]
        _cache_roles(conn, card, roles, source="llm")
        return roles

    return ["other"]


def classify_cards(
    conn: sqlite3.Connection,
    cards: Iterable[Card],
    llm_classify: LlmClassifier | None = None,
) -> dict[str, list[str]]:
    """Clasifica varias cartas de una vez. Devuelve nombre -> roles."""
    return {card.name: classify_card(conn, card, llm_classify) for card in cards}


def count_roles(
    conn: sqlite3.Connection,
    cards: Iterable[Card],
    llm_classify: LlmClassifier | None = None,
) -> dict[str, int]:
    """Cuenta cuántas cartas (con multiplicidad, ej. tierras básicas repetidas)
    tienen cada rol."""
    counts: dict[str, int] = {}
    for card in cards:
        for role in classify_card(conn, card, llm_classify):
            counts[role] = counts.get(role, 0) + 1
    return counts
