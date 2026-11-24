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
            image_uri TEXT,
            image_uri_back TEXT
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
            "INSERT INTO cards (oracle_id, name, name_normalized, mana_cost, cmc, type_line, "
            "oracle_text, colors, color_identity, produced_mana, legalities, image_uri) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
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
    # Carta de doble cara (transform): tiene imagen del reverso para girarla.
    conn.execute(
        "INSERT INTO cards VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            "4",
            "Delver of Secrets // Insectile Aberration",
            "delver of secrets // insectile aberration",
            "{U}",
            1.0,
            "Creature — Human Wizard // Creature — Human Insect",
            "front // back",
            json.dumps(["U"]),
            json.dumps(["U"]),
            json.dumps([]),
            json.dumps({"commander": "legal"}),
            "https://cards.scryfall.io/normal/front/delver.jpg",
            "https://cards.scryfall.io/normal/back/delver.jpg",
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
    assert response.json() == {"status": "ok", "cards_db": True, "cards_db_status": "ready"}


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


def test_analyze_with_budget_mode_ajustado_sorts_candidates_by_price(client: TestClient, monkeypatch):
    from analyzer.pipeline import AnalysisRun

    monkeypatch.setattr("analyzer.llm.load_dotenv", lambda *a, **k: None)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "fake-key-for-test")

    validated_analysis = {
        "estrategia_detectada": "control",
        "arquetipo": "artifacts",
        "puntos_fuertes": [],
        "problemas": [
            {
                "categoria": "Ramp",
                "severidad": "alta",
                "explicacion": "poco ramp",
                "candidatas_sugeridas": [
                    {"carta": "Arcane Signet", "rol": "ramp", "motivo": "ramp cara"},
                    {"carta": "Sol Ring", "rol": "ramp", "motivo": "ramp eficiente"},
                ],
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
    monkeypatch.setattr(
        "analyzer.prices.fetch_prices", lambda conn, names: {"Sol Ring": 0.85, "Arcane Signet": 3.0}
    )

    response = client.post(
        "/analyze",
        json={"deck_text": "Deck:\n1 Sol Ring\n2 Forest\n", "ai": True, "budget_mode": "ajustado"},
    )

    assert response.status_code == 200
    candidatas = response.json()["analisis"]["problemas"][0]["candidatas_sugeridas"]
    assert [c["carta"] for c in candidatas] == ["Sol Ring", "Arcane Signet"]
    assert candidatas[0]["precio_eur"] == 0.85


def test_analyze_exposes_combos_detectados_from_the_payload(client: TestClient, monkeypatch):
    from analyzer.pipeline import AnalysisRun

    monkeypatch.setattr("analyzer.llm.load_dotenv", lambda *a, **k: None)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "fake-key-for-test")

    validated_analysis = {
        "estrategia_detectada": "control",
        "arquetipo": "artifacts",
        "puntos_fuertes": [],
        "problemas": [],
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


def test_analyze_shows_prices_even_without_budget_mode(client: TestClient, monkeypatch):
    # Bug real (versión previa del esquema): los precios no aparecian en el
    # informe si no se marcaba un presupuesto, porque antes solo se
    # consultaban en ese caso. El precio es informacion util por si sola.
    from analyzer.pipeline import AnalysisRun

    monkeypatch.setattr("analyzer.llm.load_dotenv", lambda *a, **k: None)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "fake-key-for-test")

    validated_analysis = {
        "estrategia_detectada": "control",
        "arquetipo": "artifacts",
        "puntos_fuertes": [],
        "problemas": [
            {
                "categoria": "Ramp",
                "severidad": "media",
                "explicacion": "poco ramp",
                "candidatas_sugeridas": [
                    {"carta": "Sol Ring", "rol": "ramp", "motivo": "ramp eficiente"}
                ],
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
    candidata = response.json()["analisis"]["problemas"][0]["candidatas_sugeridas"][0]
    assert candidata["precio_eur"] == 0.85


def test_analyze_without_db_returns_503(tmp_path, monkeypatch):
    monkeypatch.setattr(api_module.cards_module, "DEFAULT_DB_PATH", tmp_path / "missing.db")
    client = TestClient(api_module.app)
    response = client.post("/analyze", json={"deck_text": "Deck:\n1 Sol Ring\n"})
    assert response.status_code == 503


def test_simulate_happy_path_returns_expected_shape(client: TestClient):
    response = client.post(
        "/simulate",
        json={
            "deck_text": "Commander:\n1 Atraxa, Praetors' Voice\n\nDeck:\n1 Sol Ring\n37 Forest\n",
            "n_sims": 100,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["simulaciones"] == 100
    assert "turno_comandante_lanzable" in body
    assert "media" in body["turno_comandante_lanzable"]
    assert "por_turno" in body["turno_comandante_lanzable"]
    assert "prob_mana_screw_turno_3" in body
    assert "primera_rampa" in body
    assert "curva_mana_media" in body
    assert "prob_mulligan" in body
    assert body["no_encontradas"] == []


def test_simulate_without_commander_returns_400(client: TestClient):
    response = client.post(
        "/simulate", json={"deck_text": "Deck:\n1 Sol Ring\n37 Forest\n", "n_sims": 100}
    )
    assert response.status_code == 400


def test_simulate_without_deck_text_or_moxfield_url_returns_400(client: TestClient):
    response = client.post("/simulate", json={"n_sims": 100})
    assert response.status_code == 400


def test_simulate_rejects_n_sims_out_of_bounds(client: TestClient):
    response = client.post(
        "/simulate",
        json={
            "deck_text": "Commander:\n1 Atraxa, Praetors' Voice\n\nDeck:\n1 Sol Ring\n37 Forest\n",
            "n_sims": 1,
        },
    )
    assert response.status_code == 422


def test_simulate_without_db_returns_503(tmp_path, monkeypatch):
    monkeypatch.setattr(api_module.cards_module, "DEFAULT_DB_PATH", tmp_path / "missing.db")
    client = TestClient(api_module.app)
    response = client.post(
        "/simulate",
        json={"deck_text": "Commander:\n1 Atraxa\n\nDeck:\n1 Sol Ring\n", "n_sims": 100},
    )
    assert response.status_code == 503


@pytest.fixture
def missing_db(tmp_path, monkeypatch):
    db_path = tmp_path / "missing.db"
    monkeypatch.setattr(api_module.cards_module, "DEFAULT_DB_PATH", db_path)
    monkeypatch.setitem(api_module._db_download, "status", "idle")
    monkeypatch.setitem(api_module._db_download, "error", None)
    return db_path


def test_analyze_while_db_downloading_explains_it(missing_db, monkeypatch):
    monkeypatch.setitem(api_module._db_download, "status", "downloading")
    client = TestClient(api_module.app)

    response = client.post("/analyze", json={"deck_text": "Deck:\n1 Sol Ring\n"})
    assert response.status_code == 503
    assert "Se está descargando" in response.json()["detail"]
    assert client.get("/health").json()["cards_db_status"] == "downloading"


def test_simulate_after_failed_download_reports_error(missing_db, monkeypatch):
    monkeypatch.setitem(api_module._db_download, "status", "error")
    monkeypatch.setitem(api_module._db_download, "error", "sin conexión")
    client = TestClient(api_module.app)

    response = client.post("/simulate", json={"deck_text": "Deck:\n1 Sol Ring\n"})
    assert response.status_code == 503
    assert "sin conexión" in response.json()["detail"]


def test_startup_downloads_missing_db_in_background(missing_db, monkeypatch):
    calls = []

    def fake_build(db_path, log):
        calls.append(db_path)
        make_db(db_path)
        return 1

    monkeypatch.setattr(api_module.scryfall_db, "build_database", fake_build)
    monkeypatch.delenv("AUTO_DOWNLOAD_CARDS_DB", raising=False)

    with TestClient(api_module.app):  # el context manager ejecuta el lifespan
        for thread in __import__("threading").enumerate():
            if thread.name == "cards-db-download":
                thread.join(timeout=5)

    assert calls == [missing_db]
    assert api_module._cards_db_status() == "ready"


def test_startup_download_can_be_disabled(missing_db, monkeypatch):
    monkeypatch.setenv("AUTO_DOWNLOAD_CARDS_DB", "0")
    monkeypatch.setattr(
        api_module.scryfall_db, "build_database", lambda *a, **k: pytest.fail("no debería descargar")
    )
    assert api_module.start_cards_db_download_if_missing() is False
    assert api_module._cards_db_status() == "missing"


def test_analyze_returns_back_images_only_for_double_faced_cards(client: TestClient):
    response = client.post(
        "/analyze",
        json={
            "deck_text": "Commander:\n1 Atraxa, Praetors' Voice\n\nDeck:\n1 Sol Ring\n"
            "1 Delver of Secrets // Insectile Aberration\n"
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["card_back_images"] == {
        "Delver of Secrets // Insectile Aberration": "https://cards.scryfall.io/normal/back/delver.jpg"
    }
    assert body["card_images"]["Delver of Secrets // Insectile Aberration"] == (
        "https://cards.scryfall.io/normal/front/delver.jpg"
    )
