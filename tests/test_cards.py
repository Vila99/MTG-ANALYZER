import json
import sqlite3

from analyzer.cards import get_card_by_name, resolve_deck
from analyzer.parser import DeckEntry, ParsedDeck


def make_test_db() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript(
        """
        CREATE TABLE cards (
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
        """
    )
    conn.execute(
        "INSERT INTO cards VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        (
            "1",
            "Sol Ring",
            "sol ring",
            "{1}",
            1.0,
            "Artifact",
            "",
            json.dumps([]),
            json.dumps([]),
            json.dumps([]),
            json.dumps({"commander": "legal"}),
        ),
    )
    conn.execute(
        "INSERT INTO cards VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        (
            "2",
            "Strength of the Harvest // Haven of the Harvest",
            "strength of the harvest // haven of the harvest",
            "{2}{G}",
            3.0,
            "Sorcery // Land",
            "",
            json.dumps(["G"]),
            json.dumps(["G"]),
            json.dumps([]),
            json.dumps({"commander": "legal"}),
        ),
    )
    conn.commit()
    return conn


def test_exact_name_match():
    conn = make_test_db()
    card = get_card_by_name(conn, "Sol Ring")
    assert card is not None
    assert card.name == "Sol Ring"


def test_double_faced_card_matches_front_face_name():
    conn = make_test_db()
    card = get_card_by_name(conn, "Strength of the Harvest")
    assert card is not None
    assert card.name == "Strength of the Harvest // Haven of the Harvest"


def test_unknown_card_returns_none():
    conn = make_test_db()
    assert get_card_by_name(conn, "Not A Real Card") is None


def test_resolve_deck_expands_quantities_and_resolves_commander():
    conn = make_test_db()
    parsed = ParsedDeck(
        commanders=["Sol Ring"],  # no es un comandante real, pero sirve para probar la resolución
        cards=[DeckEntry(quantity=2, name="Strength of the Harvest")],
    )

    commanders, deck_cards, missing = resolve_deck(conn, parsed)

    assert [c.name for c in commanders] == ["Sol Ring"]
    assert [c.name for c in deck_cards] == [
        "Strength of the Harvest // Haven of the Harvest",
        "Strength of the Harvest // Haven of the Harvest",
    ]
    assert missing == []


def test_resolve_deck_reports_missing_cards():
    conn = make_test_db()
    parsed = ParsedDeck(
        commanders=["Phantom Commander"],
        cards=[DeckEntry(quantity=1, name="Sol Ring"), DeckEntry(quantity=1, name="Phantom Card")],
    )

    commanders, deck_cards, missing = resolve_deck(conn, parsed)

    assert commanders == []
    assert [c.name for c in deck_cards] == ["Sol Ring"]
    assert missing == ["Phantom Commander", "Phantom Card"]
