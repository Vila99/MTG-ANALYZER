"""Precios reales de cartas, vía Scryfall (que agrega precios de Cardmarket
en euros y de TCGplayer en dólares; no hay que scrapear Cardmarket).

``POST /cards/collection`` resuelve hasta 75 cartas por petición, así que
solo se usa para el puñado de cortes/añadidos de un análisis concreto, no
para todo el pool de candidatas. Los precios se cachean en SQLite con una
fecha, para no volver a pedir el mismo nombre en cada análisis.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone

import requests

from analyzer.cards import normalize_name

COLLECTION_URL = "https://api.scryfall.com/cards/collection"
USER_AGENT = "MTG-Commander-Deck-Analyzer/0.1 (contacto: ver README)"
BATCH_SIZE = 75
DEFAULT_MAX_AGE_DAYS = 7


def ensure_price_cache_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS card_prices (
            name_normalized TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            eur REAL,
            fetched_at TEXT NOT NULL
        )
        """
    )


def _get_cached_price(
    conn: sqlite3.Connection, name: str, max_age_days: int
) -> tuple[bool, float | None]:
    """Devuelve ``(en_cache, precio)``. ``en_cache`` es False si no hay
    entrada o si ya caducó (más vieja que ``max_age_days``)."""
    row = conn.execute(
        "SELECT eur, fetched_at FROM card_prices WHERE name_normalized = ?",
        (normalize_name(name),),
    ).fetchone()
    if row is None:
        return False, None
    eur, fetched_at = row
    fetched = datetime.fromisoformat(fetched_at)
    if datetime.now(timezone.utc) - fetched > timedelta(days=max_age_days):
        return False, None
    return True, eur


def _cache_price(conn: sqlite3.Connection, name: str, eur: float | None) -> None:
    conn.execute(
        """
        INSERT INTO card_prices (name_normalized, name, eur, fetched_at) VALUES (?, ?, ?, ?)
        ON CONFLICT(name_normalized) DO UPDATE SET
            name = excluded.name, eur = excluded.eur, fetched_at = excluded.fetched_at
        """,
        (normalize_name(name), name, eur, datetime.now(timezone.utc).isoformat()),
    )


def _fetch_batch_from_scryfall(names: list[str]) -> dict[str, float | None]:
    """Una sola llamada a ``/cards/collection`` para hasta 75 nombres."""
    payload = {"identifiers": [{"name": name} for name in names]}
    response = requests.post(
        COLLECTION_URL,
        json=payload,
        headers={"User-Agent": USER_AGENT},
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()

    prices: dict[str, float | None] = {}
    for card in data.get("data", []):
        eur = card["prices"].get("eur")
        prices[card["name"]] = float(eur) if eur is not None else None
    # Scryfall devuelve el nombre canónico, que puede no ser idéntico al
    # pedido (mayúsculas, acentos); se empareja por nombre normalizado.
    by_normalized = {normalize_name(name): price for name, price in prices.items()}
    return {name: by_normalized.get(normalize_name(name)) for name in names}


def fetch_prices(
    conn: sqlite3.Connection,
    names: list[str],
    max_age_days: int = DEFAULT_MAX_AGE_DAYS,
) -> dict[str, float | None]:
    """Precio en euros (Cardmarket, vía Scryfall) de cada nombre en ``names``.

    ``None`` significa que Scryfall no tiene precio en EUR para esa carta
    (o no la encontró). Usa la caché local cuando no ha caducado; el resto
    se pide a Scryfall en lotes de ``BATCH_SIZE``."""
    ensure_price_cache_table(conn)

    result: dict[str, float | None] = {}
    to_fetch: list[str] = []
    for name in names:
        cached, price = _get_cached_price(conn, name, max_age_days)
        if cached:
            result[name] = price
        else:
            to_fetch.append(name)

    for i in range(0, len(to_fetch), BATCH_SIZE):
        batch = to_fetch[i : i + BATCH_SIZE]
        fetched = _fetch_batch_from_scryfall(batch)
        for name in batch:
            price = fetched.get(name)
            _cache_price(conn, name, price)
            result[name] = price
    conn.commit()

    return result
