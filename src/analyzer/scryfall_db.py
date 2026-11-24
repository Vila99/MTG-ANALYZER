"""Descarga el bulk data 'oracle_cards' de Scryfall y lo carga en data/cards.db.

Uso:
    python scripts/load_scryfall.py

El CLI (``analyze``) y la API también llaman a ``build_database`` cuando la
base de datos no existe todavía, para que un usuario nuevo no tenga que
ejecutar este paso a mano.

Se usa el bulk data en vez de pedir carta por carta (una sola descarga, en
vez de miles de peticiones). Si en el futuro se necesita consultar la API
en vivo carta por carta, respetar el límite de ~10 peticiones/s con pausas
de 50-100 ms y enviar un User-Agent propio.
"""

from __future__ import annotations

import gzip
import io
import json
import os
import sqlite3
from collections.abc import Callable
from pathlib import Path

import requests

BULK_DATA_INDEX_URL = "https://api.scryfall.com/bulk-data"
USER_AGENT = "MTG-Commander-Deck-Analyzer/0.1 (contacto: ver README)"

DB_PATH = Path(__file__).resolve().parents[2] / "data" / "cards.db"

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
    legalities TEXT,
    image_uri TEXT,
    image_uri_back TEXT
);
CREATE INDEX IF NOT EXISTS idx_cards_name_normalized ON cards(name_normalized);
"""

_SKIP_LAYOUTS = {"art_series", "token", "double_faced_token", "emblem", "scheme", "planar"}


def _get_bulk_data_url(session: requests.Session) -> str:
    resp = session.get(BULK_DATA_INDEX_URL, timeout=30)
    resp.raise_for_status()
    for entry in resp.json()["data"]:
        if entry["type"] == "oracle_cards":
            return entry["jsonl_download_uri"]
    raise RuntimeError("No se encontró el bulk data 'oracle_cards' en la respuesta de Scryfall")


def download_oracle_cards(session: requests.Session) -> list[dict]:
    """Descarga el archivo .jsonl.gz de 'oracle_cards' y lo devuelve como lista de dicts."""
    url = _get_bulk_data_url(session)
    resp = session.get(url, timeout=180)
    resp.raise_for_status()
    with gzip.GzipFile(fileobj=io.BytesIO(resp.content)) as gz:
        return [json.loads(line) for line in gz if line.strip()]


def _normalize_name(name: str) -> str:
    return name.strip().lower()


def _card_row(card: dict) -> tuple | None:
    if card.get("layout") in _SKIP_LAYOUTS or card.get("set_type") == "memorabilia":
        return None

    # Las cartas de doble cara (transform, modal_dfc...) traen el coste, el
    # texto oracle y las imágenes en 'card_faces'; se usa la cara frontal
    # como referencia (es la que se suele nombrar en una lista de deck).
    faces = card.get("card_faces")
    mana_cost = card.get("mana_cost") or (faces[0].get("mana_cost", "") if faces else "")
    oracle_text = card.get("oracle_text") or (
        " // ".join(f.get("oracle_text", "") for f in faces) if faces else ""
    )
    image_uris = card.get("image_uris") or (faces[0].get("image_uris", {}) if faces else {})
    image_uri = image_uris.get("normal") or image_uris.get("large") or ""
    # Reverso solo para las cartas que tienen de verdad dos imágenes
    # (transform, modal_dfc...): esas no traen 'image_uris' a nivel de carta,
    # sino una por cara. Las partidas/aventuras comparten una sola imagen.
    back_uris = (
        faces[1].get("image_uris", {})
        if faces and len(faces) > 1 and not card.get("image_uris")
        else {}
    )
    image_uri_back = back_uris.get("normal") or back_uris.get("large") or ""

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
        image_uri,
        image_uri_back,
    )


def _ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
    columns = {row[1] for row in conn.execute("PRAGMA table_info(cards)")}
    if "image_uri" not in columns:
        conn.execute("ALTER TABLE cards ADD COLUMN image_uri TEXT")
    if "image_uri_back" not in columns:
        conn.execute("ALTER TABLE cards ADD COLUMN image_uri_back TEXT")


def load_into_sqlite(cards_data: list[dict], db_path: Path = DB_PATH) -> int:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    try:
        _ensure_schema(conn)
        rows = [row for card in cards_data if (row := _card_row(card)) is not None]
        conn.executemany(
            """
            INSERT INTO cards (
                oracle_id, name, name_normalized, mana_cost, cmc,
                type_line, oracle_text, colors, color_identity,
                produced_mana, legalities, image_uri, image_uri_back
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                legalities=excluded.legalities,
                image_uri=excluded.image_uri,
                image_uri_back=excluded.image_uri_back
            """,
            rows,
        )
        conn.commit()
        return len(rows)
    finally:
        conn.close()


def _new_session() -> requests.Session:
    session = requests.Session()
    session.headers["User-Agent"] = USER_AGENT
    session.headers["Accept"] = "application/json;q=0.9,*/*;q=0.8"
    return session


def build_database(
    db_path: Path = DB_PATH,
    log: Callable[[str], None] = print,
    session: requests.Session | None = None,
) -> int:
    """Descarga las cartas de Scryfall y las carga en ``db_path``.

    Si la base de datos ya existe, actualiza las cartas en sitio (las
    cachés de roles, precios y combos se conservan). Si no existe, se
    construye en un archivo temporal y solo se renombra al final, para que
    una descarga interrumpida no deje una ``cards.db`` a medias que el
    resto de la app daría por buena.
    """
    session = session or _new_session()
    log("Consultando el índice de bulk data de Scryfall...")
    cards_data = download_oracle_cards(session)

    if db_path.exists():
        log(f"Descargadas {len(cards_data)} cartas. Actualizando {db_path}...")
        count = load_into_sqlite(cards_data, db_path)
    else:
        log(f"Descargadas {len(cards_data)} cartas. Creando {db_path}...")
        tmp_path = db_path.with_name(db_path.name + ".tmp")
        tmp_path.unlink(missing_ok=True)
        try:
            count = load_into_sqlite(cards_data, tmp_path)
            os.replace(tmp_path, db_path)
        finally:
            tmp_path.unlink(missing_ok=True)

    log(f"Listo: {count} cartas cargadas en la base de datos.")
    return count


def main() -> int:
    build_database(DB_PATH)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
