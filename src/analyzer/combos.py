"""Detecta combos reales dentro del deck vía Commander Spellbook — no hay
forma de verificar esto desde los datos de Scryfall.

No hay API oficial/documentada de Commander Spellbook, pero es una API
REST abierta sin autenticación (su propio repo es público y hay un
cliente npm oficial), así que se consulta con moderación: una llamada
por análisis, cacheada por el conjunto exacto de cartas del deck (los
combos catalogados no cambian de un día para otro).
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import datetime, timedelta, timezone

import requests

FIND_COMBOS_URL = "https://backend.commanderspellbook.com/find-my-combos"
USER_AGENT = "MTG-Commander-Deck-Analyzer/0.1 (contacto: ver README)"
DEFAULT_MAX_AGE_DAYS = 30


def ensure_combo_cache_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS combo_cache (
            deck_hash TEXT PRIMARY KEY,
            combos TEXT NOT NULL,
            fetched_at TEXT NOT NULL
        )
        """
    )


def _deck_hash(card_names: list[str], commander_names: list[str]) -> str:
    key = "|".join(sorted(set(card_names))) + "::" + "|".join(sorted(set(commander_names)))
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


def _parse_included_combos(data: dict) -> list[dict]:
    included = (data.get("results") or {}).get("included", [])
    combos = []
    for combo in included:
        cards = [use["card"]["name"] for use in combo.get("uses", []) if use.get("card")]
        produces = [p["feature"]["name"] for p in combo.get("produces", []) if p.get("feature")]
        if not cards:
            continue
        combos.append({"cartas": cards, "produce": produces, "descripcion": combo.get("description", "")})
    return combos


def find_combos(
    conn: sqlite3.Connection,
    card_names: list[str],
    commander_names: list[str],
    max_age_days: int = DEFAULT_MAX_AGE_DAYS,
) -> list[dict]:
    """Combos de Commander Spellbook que se completan con las cartas dadas.

    Nunca lanza: si Spellbook no responde o da un error, devuelve ``[]``
    en vez de bloquear el análisis (los combos son un dato adicional, no
    algo de lo que dependa el resto del pipeline)."""
    ensure_combo_cache_table(conn)
    deck_hash = _deck_hash(card_names, commander_names)

    row = conn.execute(
        "SELECT combos, fetched_at FROM combo_cache WHERE deck_hash = ?", (deck_hash,)
    ).fetchone()
    if row is not None:
        combos_json, fetched_at = row
        if datetime.now(timezone.utc) - datetime.fromisoformat(fetched_at) <= timedelta(days=max_age_days):
            return json.loads(combos_json)

    payload = {
        "main": [{"card": name} for name in card_names],
        "commanders": [{"card": name} for name in commander_names],
    }
    try:
        response = requests.post(
            FIND_COMBOS_URL, json=payload, headers={"User-Agent": USER_AGENT}, timeout=30
        )
        response.raise_for_status()
        data = response.json()
    except (requests.RequestException, ValueError):
        return []

    combos = _parse_included_combos(data)

    conn.execute(
        """
        INSERT INTO combo_cache (deck_hash, combos, fetched_at) VALUES (?, ?, ?)
        ON CONFLICT(deck_hash) DO UPDATE SET combos = excluded.combos, fetched_at = excluded.fetched_at
        """,
        (deck_hash, json.dumps(combos), datetime.now(timezone.utc).isoformat()),
    )
    conn.commit()
    return combos
