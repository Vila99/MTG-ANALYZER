import json
import sqlite3
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from analyzer import api as api_module


def make_db(path: Path) -> None:
    conn = sqlite3.connect(path)
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
            legalities TEXT,
            image_uri TEXT
        );
        """
    )
    rows = [
        (
            "1",
            "Atraxa, Praetors' Voice",
            "atraxa, praetors' voice",
            "{G}{W}{U}{B}",
            4.0,
            "Legendary Creature — Phyrexian Angel",
            "Flying, vigilance, deathtouch, lifelink.",
            ["W", "U", "B", "G"],
            ["W", "U", "B", "G"],
            [],
            {"commander": "legal"},
            "https://cards.scryfall.io/normal/atraxa.jpg",
        ),
        (
            "2",
            "Sol Ring",
            "sol ring",
            "{1}",
            1.0,
            "Artifact",
            "{T}: Add {C}{C}.",
            [],
            [],
            [],
            {"commander": "legal"},
            "https://cards.scryfall.io/normal/sol-ring.jpg",
        ),
        (
            "3",
            "Forest",
            "forest",
            "",
            0.0,
            "Basic Land — Forest",
            "({T}: Add {G}.)",
            [],
            ["G"],
            ["G"],
            {"commander": "legal"},
            "",
        ),
    ]
    for r in rows:
        conn.execute(
            "INSERT INTO cards VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                r[0],
                r[1],
                r[2],
                r[3],
                r[4],
                r[5],
                r[6],
                json.dumps(r[7]),
                json.dumps(r[8]),
                json.dumps(r[9]),
                json.dumps(r[10]),
                r[11],
            ),
        )
    conn.commit()
    conn.close()


@pytest.fixture
def client(tmp_path, monkeypatch) -> TestClient:
    db_path = tmp_path / "cards.db"
    make_db(db_path)
    monkeypatch.setattr(api_module.cards_module, "DEFAULT_DB_PATH", db_path)
    return TestClient(api_module.app)


def test_health_reports_db_present(client: TestClient):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "cards_db": True}


def test_analyze_happy_path(client: TestClient):
    response = client.post(
        "/analyze",
        json={"deck_text": "Commander:\n1 Atraxa, Praetors' Voice\n\nDeck:\n1 Sol Ring\n2 Forest\n"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["comandantes"] == ["Atraxa, Praetors' Voice"]
    assert body["tamano_deck"] == 4
    assert body["tierras"] == 2
    assert body["no_encontradas"] == []
    assert "analisis" not in body
    assert body["card_images"]["Atraxa, Praetors' Voice"] == "https://cards.scryfall.io/normal/atraxa.jpg"
    assert body["card_images"]["Sol Ring"] == "https://cards.scryfall.io/normal/sol-ring.jpg"
    assert "Forest" not in body["card_images"]  # sin image_uri real, se omite


def test_analyze_uses_explicit_commander_field(client: TestClient):
    response = client.post(
        "/analyze",
        json={"deck_text": "Deck:\n1 Sol Ring\n", "commander": "Atraxa, Praetors' Voice"},
    )
    assert response.status_code == 200
    assert response.json()["comandantes"] == ["Atraxa, Praetors' Voice"]


def test_analyze_does_not_duplicate_commander_already_in_deck_text(client: TestClient):
    response = client.post(
        "/analyze",
        json={
            "deck_text": "Commander:\n1 Atraxa, Praetors' Voice\n\nDeck:\n1 Sol Ring\n",
            "commander": "Atraxa, Praetors' Voice",
        },
    )
    assert response.status_code == 200
    assert response.json()["comandantes"] == ["Atraxa, Praetors' Voice"]


def test_analyze_reports_missing_cards(client: TestClient):
    response = client.post("/analyze", json={"deck_text": "Deck:\n1 Totally Fake Card\n"})
    assert response.status_code == 200
    assert response.json()["no_encontradas"] == ["Totally Fake Card"]


def test_analyze_ai_without_api_key_returns_400(client: TestClient, monkeypatch):
    # Evita que un .env real en el repo del desarrollador filtre la key aquí.
    monkeypatch.setattr("analyzer.llm.load_dotenv", lambda *a, **k: None)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    response = client.post(
        "/analyze",
        json={"deck_text": "Deck:\n1 Sol Ring\n", "ai": True},
    )
    assert response.status_code == 400
    assert "ANTHROPIC_API_KEY" in response.json()["detail"]


def test_analyze_without_db_returns_503(tmp_path, monkeypatch):
    monkeypatch.setattr(api_module.cards_module, "DEFAULT_DB_PATH", tmp_path / "missing.db")
    client = TestClient(api_module.app)
    response = client.post("/analyze", json={"deck_text": "Deck:\n1 Sol Ring\n"})
    assert response.status_code == 503


def test_analyze_rejects_bracket_out_of_range(client: TestClient):
    response = client.post("/analyze", json={"deck_text": "Deck:\n1 Sol Ring\n", "bracket": 9})
    assert response.status_code == 422
