import json
import sqlite3

from analyzer.cards import Card
from analyzer.validate import validate_addition, validate_analysis


def make_db() -> sqlite3.Connection:
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

    def insert(oracle_id, name, color_identity, legal=True, type_line="Artifact"):
        conn.execute(
            "INSERT INTO cards VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (
                oracle_id,
                name,
                name.lower(),
                "",
                1.0,
                type_line,
                "",
                json.dumps(color_identity),
                json.dumps(color_identity),
                json.dumps([]),
                json.dumps({"commander": "legal" if legal else "banned"}),
            ),
        )

    insert("1", "Arcane Signet", [])
    insert("2", "Lightning Bolt", ["R"])
    insert("3", "Channel", [], legal=False)
    insert("4", "Sol Ring", [])
    insert("5", "Forest", ["G"], type_line="Basic Land — Forest")
    conn.commit()
    return conn


def make_commander(color_identity: list[str]) -> Card:
    return Card(
        name="Commander",
        mana_cost="",
        cmc=4.0,
        type_line="Legendary Creature",
        oracle_text="",
        colors=color_identity,
        color_identity=color_identity,
        produced_mana=[],
        legalities={"commander": "legal"},
    )


def test_validate_addition_rejects_nonexistent_card():
    conn = make_db()
    result = validate_addition(conn, "Not A Real Card", {"W", "U"}, set())
    assert not result.valido
    assert "no existe" in result.motivo_rechazo


def test_validate_addition_rejects_illegal_card():
    conn = make_db()
    result = validate_addition(conn, "Channel", {"W", "U", "B", "R", "G"}, set())
    assert not result.valido
    assert "legal" in result.motivo_rechazo


def test_validate_addition_rejects_outside_color_identity():
    conn = make_db()
    result = validate_addition(conn, "Lightning Bolt", {"W", "U"}, set())
    assert not result.valido
    assert "identidad de color" in result.motivo_rechazo


def test_validate_addition_rejects_duplicate_nonbasic_card():
    conn = make_db()
    result = validate_addition(conn, "Sol Ring", {"W", "U"}, {"Sol Ring"})
    assert not result.valido
    assert "ya está en el deck" in result.motivo_rechazo


def test_validate_addition_allows_duplicate_basic_land():
    conn = make_db()
    result = validate_addition(conn, "Forest", {"G"}, {"Forest"})
    assert result.valido


def test_validate_addition_accepts_valid_card():
    conn = make_db()
    result = validate_addition(conn, "Arcane Signet", {"W", "U"}, set())
    assert result.valido


def test_validate_analysis_filters_invalid_candidates_per_problema():
    conn = make_db()
    commanders = [make_commander(["W", "U"])]
    deck_cards = [
        Card(
            name="Sol Ring",
            mana_cost="",
            cmc=1.0,
            type_line="Artifact",
            oracle_text="",
            colors=[],
            color_identity=[],
            produced_mana=[],
            legalities={"commander": "legal"},
        )
    ]

    analysis = {
        "estrategia_detectada": "control",
        "arquetipo": "superfriends",
        "puntos_fuertes": [],
        "problemas": [
            {
                "categoria": "Ramp",
                "severidad": "media",
                "explicacion": "poco ramp",
                "candidatas_sugeridas": [
                    {"carta": "Arcane Signet", "rol": "ramp", "motivo": "ramp eficiente"},
                    {"carta": "Lightning Bolt", "rol": "removal", "motivo": "fuera de color"},
                    {"carta": "Channel", "rol": "ramp", "motivo": "banida"},
                    {"carta": "Sol Ring", "rol": "ramp", "motivo": "ya está en el deck"},
                ],
            }
        ],
    }

    result = validate_analysis(conn, analysis, commanders, deck_cards)

    assert result["problemas"][0]["candidatas_sugeridas"] == [
        {"carta": "Arcane Signet", "rol": "ramp", "motivo": "ramp eficiente"}
    ]
    assert result["estrategia_detectada"] == "control"
