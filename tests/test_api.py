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
    # El coste aproximado del deck se calcula siempre (no solo con --ai):
    # se mockea por defecto para que los tests no dependan de la red: los
    # que sí quieren comprobar precios concretos sobreescriben esto.
    monkeypatch.setattr("analyzer.prices.fetch_prices", lambda conn, names: {})
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


def test_analyze_includes_approximate_deck_cost_even_without_ai(client: TestClient, monkeypatch):
    monkeypatch.setattr(
        "analyzer.prices.fetch_prices", lambda conn, names: {"Sol Ring": 0.85, "Forest": None}
    )
    response = client.post(
        "/analyze",
        json={"deck_text": "Commander:\n1 Atraxa, Praetors' Voice\n\nDeck:\n1 Sol Ring\n2 Forest\n"},
    )
    assert response.status_code == 200
    assert response.json()["coste_aproximado"] == {"total_eur": 0.85, "cartas_sin_precio": ["Forest"]}


def test_analyze_fetches_deck_from_moxfield_url(client: TestClient, monkeypatch):
    monkeypatch.setattr(
        "analyzer.moxfield.requests.get",
        lambda *a, **k: type(
            "R",
            (),
            {
                "status_code": 200,
                "ok": True,
                "json": lambda self: {
                    "commanders": {"Atraxa, Praetors' Voice": {"quantity": 1}},
                    "mainboard": {"Sol Ring": {"quantity": 1}},
                },
            },
        )(),
    )
    response = client.post(
        "/analyze", json={"moxfield_url": "https://www.moxfield.com/decks/abc123"}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["comandantes"] == ["Atraxa, Praetors' Voice"]
    assert body["tamano_deck"] == 2


def test_analyze_without_deck_text_or_moxfield_url_returns_400(client: TestClient):
    response = client.post("/analyze", json={})
    assert response.status_code == 400


def test_analyze_moxfield_not_found_returns_400(client: TestClient, monkeypatch):
    monkeypatch.setattr(
        "analyzer.moxfield.requests.get",
        lambda *a, **k: type("R", (), {"status_code": 404, "ok": False})(),
    )
    response = client.post(
        "/analyze", json={"moxfield_url": "https://www.moxfield.com/decks/no-existe"}
    )
    assert response.status_code == 400


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


def test_analyze_resolves_partial_commander_name_instead_of_losing_it(client: TestClient):
    # Bug real: si el campo "Comandante" no coincide letra por letra con el
    # nombre de Scryfall, antes se perdía el comandante por completo y el
    # deck quedaba "sin comandante" en el análisis.
    response = client.post(
        "/analyze",
        json={"deck_text": "Deck:\n1 Sol Ring\n", "commander": "Atraxa"},
    )
    assert response.status_code == 200
    assert response.json()["comandantes"] == ["Atraxa, Praetors' Voice"]


def test_analyze_includes_cartas_por_rol_without_ai(client: TestClient):
    response = client.post(
        "/analyze",
        json={"deck_text": "Deck:\n1 Sol Ring\n2 Forest\n"},
    )
    assert response.status_code == 200
    body = response.json()
    assert "ramp" in body["cartas_por_rol"]
    assert "Sol Ring" in body["cartas_por_rol"]["ramp"]
    assert "land" in body["cartas_por_rol"]
    assert "Forest" in body["cartas_por_rol"]["land"]


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


def test_analyze_with_budget_enriches_additions_with_real_prices(client: TestClient, monkeypatch):
    from analyzer.pipeline import AnalysisRun

    monkeypatch.setattr("analyzer.llm.load_dotenv", lambda *a, **k: None)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "fake-key-for-test")

    validated_analysis = {
        "estrategia_detectada": "control",
        "arquetipo": "artifacts",
        "puntos_fuertes": [],
        "problemas": [{"categoria": "Ramp", "severidad": "alta", "explicacion": "poco ramp"}],
        "cortes_sugeridos": [],
        "anadidos_sugeridos": [
            {
                "carta": "Sol Ring",
                "rol": "ramp",
                "reemplaza_a": None,
                "categoria_problema": "Ramp",
                "motivo": "ramp eficiente",
            }
        ],
        "bracket": {
            "deducido": 2,
            "confianza": "alta",
            "suelo": 1,
            "estimacion_juego": 2,
            "game_changers": [],
            "senales_duras": [],
            "razones": [],
            "que_lo_moveria": {"bajar": [], "subir": []},
        },
    }
    fake_run = AnalysisRun(payload={}, raw_analysis=validated_analysis, validated_analysis=validated_analysis)
    monkeypatch.setattr("analyzer.pipeline.run_analysis", lambda *a, **k: fake_run)
    monkeypatch.setattr("analyzer.prices.fetch_prices", lambda conn, names: {"Sol Ring": 0.85})

    response = client.post(
        "/analyze",
        json={"deck_text": "Deck:\n1 Sol Ring\n2 Forest\n", "ai": True, "budget": 10},
    )

    assert response.status_code == 200
    addition = response.json()["analisis"]["anadidos_sugeridos"][0]
    assert addition["precio_eur"] == 0.85
    assert addition["incluido"] is True
    assert response.json()["analisis"]["presupuesto"] == {
        "presupuesto": 10.0,
        "coste_estimado": 0.85,
        "supera_presupuesto": False,
        "diferencia": -9.15,
    }


def test_analyze_exposes_combos_detectados_from_the_payload(client: TestClient, monkeypatch):
    from analyzer.pipeline import AnalysisRun

    monkeypatch.setattr("analyzer.llm.load_dotenv", lambda *a, **k: None)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "fake-key-for-test")

    validated_analysis = {
        "estrategia_detectada": "control",
        "arquetipo": "artifacts",
        "puntos_fuertes": [],
        "problemas": [],
        "cortes_sugeridos": [],
        "anadidos_sugeridos": [],
        "bracket": {
            "deducido": 4,
            "confianza": "alta",
            "suelo": 4,
            "estimacion_juego": 4,
            "game_changers": [],
            "senales_duras": [],
            "razones": [],
            "que_lo_moveria": {"bajar": [], "subir": []},
        },
    }
    combo = {
        "cartas": ["Thassa's Oracle", "Demonic Consultation"],
        "produce": ["Win the game"],
        "descripcion": "Exile library, win.",
        "velocidad": "temprano",
    }
    fake_run = AnalysisRun(
        payload={"bracket_suelo": {"floor": 4, "combos": [combo]}},
        raw_analysis=validated_analysis,
        validated_analysis=validated_analysis,
    )
    monkeypatch.setattr("analyzer.pipeline.run_analysis", lambda *a, **k: fake_run)

    response = client.post(
        "/analyze", json={"deck_text": "Deck:\n1 Sol Ring\n", "ai": True}
    )

    assert response.status_code == 200
    assert response.json()["analisis"]["combos_detectados"] == [combo]


def test_analyze_shows_prices_even_without_budget(client: TestClient, monkeypatch):
    # Bug real: los precios no aparecian en el informe si no se marcaba un
    # presupuesto, porque antes solo se consultaban en ese caso.
    from analyzer.pipeline import AnalysisRun

    monkeypatch.setattr("analyzer.llm.load_dotenv", lambda *a, **k: None)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "fake-key-for-test")

    validated_analysis = {
        "estrategia_detectada": "control",
        "arquetipo": "artifacts",
        "puntos_fuertes": [],
        "problemas": [],
        "cortes_sugeridos": [],
        "anadidos_sugeridos": [
            {
                "carta": "Sol Ring",
                "rol": "ramp",
                "reemplaza_a": None,
                "categoria_problema": None,
                "motivo": "ramp eficiente",
            }
        ],
        "bracket": {
            "deducido": 2,
            "confianza": "alta",
            "suelo": 1,
            "estimacion_juego": 2,
            "game_changers": [],
            "senales_duras": [],
            "razones": [],
            "que_lo_moveria": {"bajar": [], "subir": []},
        },
    }
    fake_run = AnalysisRun(payload={}, raw_analysis=validated_analysis, validated_analysis=validated_analysis)
    monkeypatch.setattr("analyzer.pipeline.run_analysis", lambda *a, **k: fake_run)
    monkeypatch.setattr("analyzer.prices.fetch_prices", lambda conn, names: {"Sol Ring": 0.85})

    response = client.post(
        "/analyze",
        json={"deck_text": "Deck:\n1 Sol Ring\n2 Forest\n", "ai": True},
    )

    assert response.status_code == 200
    addition = response.json()["analisis"]["anadidos_sugeridos"][0]
    assert addition["precio_eur"] == 0.85
    assert "presupuesto" not in response.json()["analisis"]


def test_analyze_without_db_returns_503(tmp_path, monkeypatch):
    monkeypatch.setattr(api_module.cards_module, "DEFAULT_DB_PATH", tmp_path / "missing.db")
    client = TestClient(api_module.app)
    response = client.post("/analyze", json={"deck_text": "Deck:\n1 Sol Ring\n"})
    assert response.status_code == 503
