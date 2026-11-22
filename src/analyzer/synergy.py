"""Pool de cartas candidatas por sinergia con el comandante.

El código decide qué cartas son candidatas (búsqueda determinista sobre el
texto oracle ya cargado en ``cards.db``); Claude solo interpreta qué
palabras clave mecánicas buscar (ver ``analyzer.llm.extract_synergy_keywords_with_haiku``)
y, más tarde, cuáles de las candidatas encajan mejor en el deck. La
extracción de palabras clave se cachea por comandante, igual que
``analyzer.roles`` cachea la clasificación por rol de cada carta.
"""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Callable

from analyzer.cards import Card, row_to_card, normalize_name

LlmKeywordExtractor = Callable[[Card], list[str]]

DEFAULT_POOL_LIMIT = 30


def ensure_synergy_cache_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS commander_synergy_keywords (
            name_normalized TEXT PRIMARY KEY,
            keywords TEXT NOT NULL
        )
        """
    )


def get_cached_keywords(conn: sqlite3.Connection, commander: Card) -> list[str] | None:
    row = conn.execute(
        "SELECT keywords FROM commander_synergy_keywords WHERE name_normalized = ?",
        (normalize_name(commander.name),),
    ).fetchone()
    if row is None:
        return None
    return json.loads(row[0])


def _cache_keywords(conn: sqlite3.Connection, commander: Card, keywords: list[str]) -> None:
    conn.execute(
        """
        INSERT INTO commander_synergy_keywords (name_normalized, keywords) VALUES (?, ?)
        ON CONFLICT(name_normalized) DO UPDATE SET keywords = excluded.keywords
        """,
        (normalize_name(commander.name), json.dumps(keywords)),
    )
    conn.commit()


def get_synergy_keywords(
    conn: sqlite3.Connection,
    commander: Card,
    llm_extract: LlmKeywordExtractor | None = None,
) -> list[str]:
    """Palabras clave mecánicas del comandante: caché -> Haiku si se da un
    extractor. Devuelve ``[]`` si no hay caché ni extractor (no se cachea
    ese resultado vacío, para poder reintentar luego con Haiku disponible)."""
    ensure_synergy_cache_table(conn)

    cached = get_cached_keywords(conn, commander)
    if cached is not None:
        return cached

    if llm_extract is None:
        return []

    keywords = llm_extract(commander)
    _cache_keywords(conn, commander, keywords)
    return keywords


def find_candidates_by_keywords(
    conn: sqlite3.Connection,
    keywords: list[str],
    color_identity: list[str],
    exclude_names: set[str],
    limit: int = DEFAULT_POOL_LIMIT,
) -> list[Card]:
    """Busca cartas cuyo texto oracle contenga, literalmente, alguna de las
    ``keywords``, dentro de la identidad de color dada y legales en
    Commander. Ordena por cuántas keywords distintas comparte cada carta
    (más coincidencias -> más arriba), para priorizar cartas con varias
    sinergias con el comandante sobre las que solo encajan por una."""
    if not keywords:
        return []

    identity = set(color_identity)
    clauses = " OR ".join("LOWER(oracle_text) LIKE ?" for _ in keywords)
    params = [f"%{kw.lower()}%" for kw in keywords]
    # Límite generoso en SQL: el recuento de coincidencias y el límite final
    # se aplican en Python, ya filtrados por identidad de color y legalidad.
    rows = conn.execute(
        f"SELECT * FROM cards WHERE ({clauses}) LIMIT 500",  # noqa: S608 - clauses son placeholders fijos, no interpolación de datos
        params,
    ).fetchall()

    scored: list[tuple[int, Card]] = []
    for row in rows:
        card = row_to_card(row)
        if card.name in exclude_names:
            continue
        if not card.is_legal("commander"):
            continue
        if not set(card.color_identity).issubset(identity):
            continue
        text = card.oracle_text.lower()
        score = sum(1 for kw in keywords if kw.lower() in text)
        if score > 0:
            scored.append((score, card))

    scored.sort(key=lambda item: (-item[0], item[1].name))
    return [card for _, card in scored[:limit]]


def build_candidate_pool(
    conn: sqlite3.Connection,
    commanders: list[Card],
    deck_cards: list[Card],
    llm_extract: LlmKeywordExtractor | None = None,
    limit: int = DEFAULT_POOL_LIMIT,
) -> list[Card]:
    """Construye el pool de candidatas para los comandantes dados: une las
    palabras clave de todos, busca cartas que las compartan dentro de la
    identidad de color combinada y excluye lo que ya está en el deck."""
    if not commanders:
        return []

    keywords: list[str] = []
    seen_keywords: set[str] = set()
    for commander in commanders:
        for kw in get_synergy_keywords(conn, commander, llm_extract):
            normalized = kw.lower()
            if normalized not in seen_keywords:
                seen_keywords.add(normalized)
                keywords.append(kw)

    color_identity: list[str] = []
    seen_colors: set[str] = set()
    for commander in commanders:
        for color in commander.color_identity:
            if color not in seen_colors:
                seen_colors.add(color)
                color_identity.append(color)

    exclude_names = {c.name for c in commanders} | {c.name for c in deck_cards}
    return find_candidates_by_keywords(conn, keywords, color_identity, exclude_names, limit)
