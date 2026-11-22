"""Acceso a la base de datos local de cartas (generada por scripts/load_scryfall.py)."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path

from analyzer.parser import ParsedDeck

DEFAULT_DB_PATH = Path(__file__).resolve().parents[2] / "data" / "cards.db"


@dataclass(frozen=True)
class Card:
    name: str
    mana_cost: str
    cmc: float
    type_line: str
    oracle_text: str
    colors: list[str]
    color_identity: list[str]
    produced_mana: list[str]
    legalities: dict[str, str]
    image_uri: str = ""

    @property
    def is_land(self) -> bool:
        return "Land" in self.type_line

    def is_legal(self, format_name: str = "commander") -> bool:
        return self.legalities.get(format_name) == "legal"


def normalize_name(name: str) -> str:
    return name.strip().lower()


def connect(db_path: Path | str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def _row_to_card(row: sqlite3.Row) -> Card:
    keys = row.keys()
    return Card(
        name=row["name"],
        mana_cost=row["mana_cost"] or "",
        cmc=row["cmc"] or 0.0,
        type_line=row["type_line"] or "",
        oracle_text=row["oracle_text"] or "",
        colors=json.loads(row["colors"] or "[]"),
        color_identity=json.loads(row["color_identity"] or "[]"),
        produced_mana=json.loads(row["produced_mana"] or "[]"),
        legalities=json.loads(row["legalities"] or "{}"),
        # Compatibilidad con bases de datos generadas antes de añadir esta
        # columna: sin ella, no hay imagen hasta recargar con load_scryfall.py.
        image_uri=(row["image_uri"] or "") if "image_uri" in keys else "",
    )


def get_card_by_name(conn: sqlite3.Connection, name: str) -> Card | None:
    normalized = normalize_name(name)
    row = conn.execute(
        "SELECT * FROM cards WHERE name_normalized = ?",
        (normalized,),
    ).fetchone()
    if row is None:
        # Cartas de doble cara (MDFC/transform) se guardan como "Cara A // Cara B";
        # las listas de deck suelen referenciarlas solo por la cara frontal.
        row = conn.execute(
            "SELECT * FROM cards WHERE name_normalized LIKE ? LIMIT 1",
            (f"{normalized} // %",),
        ).fetchone()
    if row is None:
        return None
    return _row_to_card(row)


def resolve_deck(
    conn: sqlite3.Connection, parsed: ParsedDeck
) -> tuple[list[Card], list[Card], list[str]]:
    """Resuelve los nombres de un ``ParsedDeck`` contra la base de datos.

    Devuelve ``(comandantes, cartas_del_deck, nombres_no_encontrados)``. Las
    cartas del deck se repiten según su cantidad (ej. 6 Forest -> 6 entradas).
    """
    commanders: list[Card] = []
    deck_cards: list[Card] = []
    missing: list[str] = []

    for name in parsed.commanders:
        card = get_card_by_name(conn, name)
        if card is None:
            missing.append(name)
        else:
            commanders.append(card)

    for entry in parsed.cards:
        card = get_card_by_name(conn, entry.name)
        if card is None:
            missing.append(entry.name)
        else:
            deck_cards.extend([card] * entry.quantity)

    return commanders, deck_cards, missing
