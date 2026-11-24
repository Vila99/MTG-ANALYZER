import json
import sqlite3
from unittest.mock import MagicMock

import pytest

from analyzer.cards import Card
from analyzer.pipeline import run_analysis


@pytest.fixture(autouse=True)
def _no_real_combo_lookups(monkeypatch):
    # Combos verificados contra Commander Spellbook: se mockea por defecto
    # para que los tests no dependan de la red.
    monkeypatch.setattr("analyzer.combos.find_combos", lambda conn, names, commanders: [])


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
        "problemas": [
            {
                "categoria": "Ramp",
                "severidad": "media",
                "explicacion": "poco ramp",
                "candidatas_sugeridas": [
                    {"carta": "Arcane Signet", "rol": "ramp", "motivo": "ramp eficiente"},
                    {"carta": "Not A Real Card", "rol": "ramp", "motivo": "no existe"},
                ],
            }
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
        params={"budget_mode": "ajustado"},
    )

    assert run.payload["comandantes"][0]["nombre"] == "Commander"
    assert "bracket_suelo" in run.payload
    assert run.payload["bracket_suelo"]["floor"] == 1  # Sol Ring no dispara ninguna señal dura
    assert run.raw_analysis == raw_analysis
    # "Not A Real Card" no existe en la BD de prueba: se descarta en la validación.
    assert run.validated_analysis["problemas"][0]["candidatas_sugeridas"] == [
        {"carta": "Arcane Signet", "rol": "ramp", "motivo": "ramp eficiente"}
    ]


def _fake_keywords_tool_use_message(keywords: list[str]):
    block = MagicMock()
    block.type = "tool_use"
    block.name = "extract_synergy_keywords"
    block.input = {"keywords": keywords}
    message = MagicMock()
    message.content = [block]
    return message


def test_run_analysis_builds_candidate_pool_from_commander_keywords_when_not_given():
    conn = make_db()
    conn.execute(
        "INSERT INTO cards VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        (
            "2",
            "Ramp Rock",
            "ramp rock",
            "{2}",
            2.0,
            "Artifact",
            "Add one mana of any color. Ramp your mana base.",
            json.dumps([]),
            json.dumps([]),
            json.dumps([]),
            json.dumps({"commander": "legal"}),
        ),
    )
    conn.commit()
    commander = make_commander()
    raw_analysis = {
        "estrategia_detectada": "control",
        "arquetipo": "artifacts",
        "puntos_fuertes": [],
        "problemas": [],
    }

    def fake_create(*, tools, **kwargs):
        if tools[0]["name"] == "extract_synergy_keywords":
            return _fake_keywords_tool_use_message(["ramp"])
        return _fake_analysis_tool_use_message(raw_analysis)

    client = MagicMock()
    client.messages.create.side_effect = fake_create

    run = run_analysis(
        client,
        conn,
        commanders=[commander],
        deck_cards=[make_deck_card()],
        card_roles={"Sol Ring": ["ramp"]},
        params={},
    )

    assert run.payload["pool_candidatas"] == [
        {"nombre": "Ramp Rock", "texto_oracle": "Add one mana of any color. Ramp your mana base."}
    ]


def test_run_analysis_does_not_rebuild_pool_when_candidate_pool_given_explicitly():
    conn = make_db()
    commander = make_commander()
    raw_analysis = {
        "estrategia_detectada": "control",
        "arquetipo": "artifacts",
        "puntos_fuertes": [],
        "problemas": [],
    }
    client = MagicMock()
    client.messages.create.return_value = _fake_analysis_tool_use_message(raw_analysis)

    run = run_analysis(
        client,
        conn,
        commanders=[commander],
        deck_cards=[make_deck_card()],
        card_roles={"Sol Ring": ["ramp"]},
        params={},
        candidate_pool=[],
    )

    assert run.payload["pool_candidatas"] == []
    client.messages.create.assert_called_once()  # solo la llamada de analyze_deck, sin extraer keywords
