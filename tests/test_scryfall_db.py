import sqlite3

import pytest

from analyzer import scryfall_db

CARD = {
    "oracle_id": "abc",
    "name": "Sol Ring",
    "layout": "normal",
    "mana_cost": "{1}",
    "cmc": 1.0,
    "type_line": "Artifact",
    "oracle_text": "{T}: Add {C}{C}.",
    "colors": [],
    "color_identity": [],
    "produced_mana": ["C"],
    "legalities": {"commander": "legal"},
    "image_uris": {"normal": "https://example/sol.jpg"},
}


def test_build_database_creates_new_db(tmp_path, monkeypatch):
    db_path = tmp_path / "cards.db"
    monkeypatch.setattr(scryfall_db, "download_oracle_cards", lambda session: [CARD])

    count = scryfall_db.build_database(db_path, log=lambda msg: None, session=object())

    assert count == 1
    assert not (tmp_path / "cards.db.tmp").exists()
    names = sqlite3.connect(db_path).execute("SELECT name FROM cards").fetchall()
    assert names == [("Sol Ring",)]


def test_interrupted_build_leaves_no_partial_db(tmp_path, monkeypatch):
    db_path = tmp_path / "cards.db"
    monkeypatch.setattr(scryfall_db, "download_oracle_cards", lambda session: [CARD])

    def fail_midway(cards_data, path):
        path.write_bytes(b"a medias")
        raise OSError("disco lleno")

    monkeypatch.setattr(scryfall_db, "load_into_sqlite", fail_midway)

    with pytest.raises(OSError):
        scryfall_db.build_database(db_path, log=lambda msg: None, session=object())

    assert not db_path.exists()
    assert not (tmp_path / "cards.db.tmp").exists()


def test_build_database_updates_existing_db_keeping_other_tables(tmp_path, monkeypatch):
    db_path = tmp_path / "cards.db"
    monkeypatch.setattr(scryfall_db, "download_oracle_cards", lambda session: [CARD])
    scryfall_db.build_database(db_path, log=lambda msg: None, session=object())
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE card_roles (name TEXT)")
    conn.execute("INSERT INTO card_roles VALUES ('Sol Ring')")
    conn.commit()
    conn.close()

    scryfall_db.build_database(db_path, log=lambda msg: None, session=object())

    rows = sqlite3.connect(db_path).execute("SELECT name FROM card_roles").fetchall()
    assert rows == [("Sol Ring",)]


TRANSFORM_CARD = {
    "oracle_id": "dfc",
    "name": "Delver of Secrets // Insectile Aberration",
    "layout": "transform",
    "cmc": 1.0,
    "type_line": "Creature — Human Wizard // Creature — Human Insect",
    "colors": ["U"],
    "color_identity": ["U"],
    "legalities": {"commander": "legal"},
    "card_faces": [
        {"name": "Delver of Secrets", "mana_cost": "{U}", "oracle_text": "front",
         "image_uris": {"normal": "https://example/front/delver.jpg"}},
        {"name": "Insectile Aberration", "mana_cost": "", "oracle_text": "back",
         "image_uris": {"normal": "https://example/back/delver.jpg"}},
    ],
}

ADVENTURE_CARD = {
    "oracle_id": "adv",
    "name": "Bonecrusher Giant // Stomp",
    "layout": "adventure",
    "mana_cost": "{2}{R} // {1}{R}",
    "cmc": 3.0,
    "type_line": "Creature — Giant // Instant — Adventure",
    "colors": ["R"],
    "color_identity": ["R"],
    "legalities": {"commander": "legal"},
    # Una sola imagen a nivel de carta: las dos "caras" comparten el mismo lado.
    "image_uris": {"normal": "https://example/bonecrusher.jpg"},
    "card_faces": [
        {"name": "Bonecrusher Giant", "mana_cost": "{2}{R}", "oracle_text": "creature"},
        {"name": "Stomp", "mana_cost": "{1}{R}", "oracle_text": "instant"},
    ],
}


def _back_images(db_path):
    rows = sqlite3.connect(db_path).execute("SELECT name, image_uri, image_uri_back FROM cards").fetchall()
    return {name: (front, back) for name, front, back in rows}


def test_double_faced_card_stores_back_face_image(tmp_path):
    db_path = tmp_path / "cards.db"
    scryfall_db.load_into_sqlite([TRANSFORM_CARD], db_path)

    front, back = _back_images(db_path)["Delver of Secrets // Insectile Aberration"]
    assert front == "https://example/front/delver.jpg"
    assert back == "https://example/back/delver.jpg"


def test_single_image_cards_have_no_back_image(tmp_path):
    db_path = tmp_path / "cards.db"
    scryfall_db.load_into_sqlite([CARD, ADVENTURE_CARD], db_path)

    images = _back_images(db_path)
    assert images["Sol Ring"][1] == ""
    # Aventura/partida: dos caras en el nombre pero una sola imagen -> no se gira.
    assert images["Bonecrusher Giant // Stomp"] == ("https://example/bonecrusher.jpg", "")


def test_existing_db_without_back_image_column_is_migrated(tmp_path):
    db_path = tmp_path / "cards.db"
    conn = sqlite3.connect(db_path)
    conn.executescript(scryfall_db.SCHEMA.replace(",\n    image_uri_back TEXT", ""))
    conn.close()

    scryfall_db.load_into_sqlite([TRANSFORM_CARD], db_path)

    assert _back_images(db_path)["Delver of Secrets // Insectile Aberration"][1] == (
        "https://example/back/delver.jpg"
    )
