"""Descarga el bulk data 'oracle_cards' de Scryfall y lo carga en data/cards.db.

Uso:
    python scripts/load_scryfall.py

Se usa el bulk data en vez de pedir carta por carta (una sola descarga, en
vez de miles de peticiones). Si en el futuro se necesita consultar la API
en vivo carta por carta, respetar el límite de ~10 peticiones/s con pausas
de 50-100 ms y enviar un User-Agent propio.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import requests

BULK_DATA_INDEX_URL = "https://api.scryfall.com/bulk-data"
USER_AGENT = "MTG-Commander-Deck-Analyzer/0.1 (contacto: ver README)"

DB_PATH = Path(__file__).resolve().parents[1] / "data" / "cards.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS cards (
    oracle_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    name_normalized TEXT NOT NULL,
    mana_cost TEXT,
    cmc REAL,
    type_line TEXT,
    oracle_text TEXT,
    colors TEXT,
    color_identity TEXT,
    produced_mana TEXT,
    legalities TEXT
);
CREATE INDEX IF NOT EXISTS idx_cards_name_normalized ON cards(name_normalized);
"""

_SKIP_LAYOUTS = {"art_series", "token", "double_faced_token", "emblem", "scheme", "planar"}


def _get_bulk_data_url(session: requests.Session) -> str:
    resp = session.get(BULK_DATA_INDEX_URL, timeout=30)
    resp.raise_for_status()
    for entry in resp.json()["data"]:
        if entry["type"] == "oracle_cards":
            return entry["download_uri"]
    raise RuntimeError("No se encontró el bulk data 'oracle_cards' en la respuesta de Scryfall")


def download_oracle_cards(session: requests.Session) -> list[dict]:
    url = _get_bulk_data_url(session)
    resp = session.get(url, timeout=180)
    resp.raise_for_status()
    return resp.json()


def _normalize_name(name: str) -> str:
    return name.strip().lower()


def _card_row(card: dict) -> tuple | None:
    if card.get("layout") in _SKIP_LAYOUTS or card.get("set_type") == "memorabilia":
        return None

    # Las cartas de doble cara (transform, modal_dfc...) traen el coste y el
    # texto oracle en 'card_faces'; se usa la cara frontal como referencia.
    faces = card.get("card_faces")
    mana_cost = card.get("mana_cost") or (faces[0].get("mana_cost", "") if faces else "")
    oracle_text = card.get("oracle_text") or (
        " // ".join(f.get("oracle_text", "") for f in faces) if faces else ""
    )

    return (
        card["oracle_id"],
        card["name"],
        _normalize_name(card["name"]),
        mana_cost or "",
        card.get("cmc", 0.0),
        card.get("type_line", ""),
        oracle_text or "",
        json.dumps(card.get("colors", [])),
        json.dumps(card.get("color_identity", [])),
        json.dumps(card.get("produced_mana") or []),
        json.dumps(card.get("legalities", {})),
    )


def load_into_sqlite(cards_data: list[dict], db_path: Path = DB_PATH) -> int:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(SCHEMA)
        rows = [row for card in cards_data if (row := _card_row(card)) is not None]
        conn.executemany(
            """
            INSERT INTO cards (
                oracle_id, name, name_normalized, mana_cost, cmc,
                type_line, oracle_text, colors, color_identity,
                produced_mana, legalities
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(oracle_id) DO UPDATE SET
                name=excluded.name,
                name_normalized=excluded.name_normalized,
                mana_cost=excluded.mana_cost,
                cmc=excluded.cmc,
                type_line=excluded.type_line,
                oracle_text=excluded.oracle_text,
                colors=excluded.colors,
                color_identity=excluded.color_identity,
                produced_mana=excluded.produced_mana,
                legalities=excluded.legalities
            """,
            rows,
        )
        conn.commit()
        return len(rows)
    finally:
        conn.close()


def main() -> int:
    session = requests.Session()
    session.headers["User-Agent"] = USER_AGENT
    session.headers["Accept"] = "application/json;q=0.9,*/*;q=0.8"

    print("Consultando el índice de bulk data de Scryfall...")
    cards_data = download_oracle_cards(session)
    print(f"Descargadas {len(cards_data)} cartas. Cargando en {DB_PATH}...")
    count = load_into_sqlite(cards_data, DB_PATH)
    print(f"Listo: {count} cartas cargadas en la base de datos.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
