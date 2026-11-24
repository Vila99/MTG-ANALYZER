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
