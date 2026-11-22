import json
import sqlite3
from unittest.mock import MagicMock

from analyzer.cards import Card
from analyzer.pipeline import run_analysis


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
    conn.execute(
        "INSERT INTO cards VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        (
            "1",
            "Arcane Signet",
            "arcane signet",
            "{2}",
            2.0,
            "Artifact",
            "",
            json.dumps([]),
            json.dumps([]),
            json.dumps([]),
            json.dumps({"commander": "legal"}),
        ),
    )
    conn.commit()
    return conn


def make_commander() -> Card:
    return Card(
        name="Commander",
        mana_cost="",
        cmc=3.0,
        type_line="Legendary Creature",
        oracle_text="",
        colors=["W", "U"],
        color_identity=["W", "U"],
        produced_mana=[],
        legalities={"commander": "legal"},
    )


def make_deck_card() -> Card:
    return Card(
        name="Sol Ring",
        mana_cost="{1}",
        cmc=1.0,
        type_line="Artifact",
        oracle_text="{T}: Add {C}{C}.",
        colors=[],
        color_identity=[],
        produced_mana=[],
        legalities={"commander": "legal"},
    )


def _fake_analysis_tool_use_message(analysis: dict):
    block = MagicMock()
    block.type = "tool_use"
    block.name = "analyze_deck"
    block.input = analysis
    message = MagicMock()
    message.content = [block]
    return message


def test_run_analysis_builds_payload_calls_claude_and_validates():
    conn = make_db()
    commander = make_commander()
    sol_ring = make_deck_card()

    raw_analysis = {
        "estrategia_detectada": "control",
        "arquetipo": "artifacts",
        "puntos_fuertes": [],
        "problemas": [],
        "cortes_sugeridos": [{"carta": "Sol Ring", "motivo": "innecesario"}],
        "anadidos_sugeridos": [
            {"carta": "Arcane Signet", "rol": "ramp", "reemplaza_a": None, "motivo": "ramp eficiente"},
            {"carta": "Not A Real Card", "rol": "ramp", "reemplaza_a": None, "motivo": "no existe"},
        ],
    }
    client = MagicMock()
    client.messages.create.return_value = _fake_analysis_tool_use_message(raw_analysis)

    run = run_analysis(
        client,
        conn,
        commanders=[commander],
        deck_cards=[sol_ring],
        card_roles={"Sol Ring": ["ramp"]},
        params={"bracket": 3},
    )

    assert run.payload["comandantes"][0]["nombre"] == "Commander"
    assert "bracket_suelo" in run.payload
    assert run.payload["bracket_suelo"]["floor"] == 1  # Sol Ring no dispara ninguna señal dura
    assert run.raw_analysis == raw_analysis
    # "Not A Real Card" no existe en la BD de prueba: se descarta en la validación.
    assert run.validated_analysis["anadidos_sugeridos"] == [
        {"carta": "Arcane Signet", "rol": "ramp", "reemplaza_a": None, "motivo": "ramp eficiente"}
    ]
    assert run.validated_analysis["cortes_sugeridos"] == raw_analysis["cortes_sugeridos"]
