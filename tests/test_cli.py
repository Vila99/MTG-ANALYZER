import json
import sqlite3
from pathlib import Path

import pytest

from analyzer.cli import main


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
            legalities TEXT
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
        ),
        (
            "3",
            "Command Tower",
            "command tower",
            "",
            0.0,
            "Land",
            "{T}: Add one mana of any color in your commander's color identity.",
            [],
            [],
            ["W", "U", "B", "R", "G"],
            {"commander": "legal"},
        ),
        (
            "4",
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
        ),
    ]
    for r in rows:
        conn.execute(
            "INSERT INTO cards VALUES (?,?,?,?,?,?,?,?,?,?,?)",
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
            ),
        )
    conn.commit()
    conn.close()


@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    path = tmp_path / "cards.db"
    make_db(path)
    return path


@pytest.fixture
def deck_path(tmp_path: Path) -> Path:
    path = tmp_path / "deck.txt"
    path.write_text(
        "Commander:\n1 Atraxa, Praetors' Voice\n\nDeck:\n1 Sol Ring\n1 Command Tower\n2 Forest\n",
        encoding="utf-8",
    )
    return path


def test_main_happy_path_returns_zero(db_path, deck_path, capsys):
    exit_code = main([str(deck_path), "--db", str(db_path)])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Atraxa" in captured.out
    assert "Tamaño del deck: 5 cartas" in captured.out


def test_main_json_output_has_expected_shape(db_path, deck_path, capsys):
    exit_code = main([str(deck_path), "--db", str(db_path), "--json"])
    captured = capsys.readouterr()

    assert exit_code == 0
    summary = json.loads(captured.out)
    assert summary["comandantes"] == ["Atraxa, Praetors' Voice"]
    assert summary["tamano_deck"] == 5
    assert summary["tierras"] == 3


def test_main_reports_missing_cards_with_exit_code_two(db_path, tmp_path, capsys):
    broken_deck_path = tmp_path / "deck_with_missing.txt"
    broken_deck_path.write_text(
        "Commander:\n1 Atraxa, Praetors' Voice\n\nDeck:\n1 Totally Fake Card\n", encoding="utf-8"
    )

    exit_code = main([str(broken_deck_path), "--db", str(db_path)])
    captured = capsys.readouterr()

    assert exit_code == 2
    assert "Totally Fake Card" in captured.out


def test_main_missing_deck_file_returns_one(db_path, tmp_path, capsys):
    exit_code = main([str(tmp_path / "does_not_exist.txt"), "--db", str(db_path)])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "No se encontró el archivo" in captured.err


def test_main_missing_db_returns_one(tmp_path, deck_path, capsys):
    exit_code = main([str(deck_path), "--db", str(tmp_path / "does_not_exist.db")])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "No se encontró la base de datos" in captured.err


def test_main_ai_without_api_key_fails_gracefully(db_path, deck_path, monkeypatch, capsys):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    exit_code = main([str(deck_path), "--db", str(db_path), "--ai"])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "ANTHROPIC_API_KEY" in captured.err
