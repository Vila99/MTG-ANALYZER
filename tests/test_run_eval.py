import json
import sqlite3
from pathlib import Path
from unittest.mock import MagicMock

import run_eval as run_eval_module


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
    conn.execute(
        "INSERT INTO cards VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        (
            "1",
            "Sol Ring",
            "sol ring",
            "{1}",
            1.0,
            "Artifact",
            "{T}: Add {C}{C}.",
            json.dumps([]),
            json.dumps([]),
            json.dumps([]),
            json.dumps({"commander": "legal"}),
        ),
    )
    conn.commit()
    conn.close()


def _fake_analysis_tool_use_message(analysis: dict):
    block = MagicMock()
    block.type = "tool_use"
    block.name = "analyze_deck"
    block.input = analysis
    message = MagicMock()
    message.content = [block]
    return message


def test_run_eval_writes_one_record_per_deck(tmp_path, monkeypatch):
    db_path = tmp_path / "cards.db"
    make_db(db_path)

    deck_path = tmp_path / "deck.txt"
    deck_path.write_text("Deck:\n1 Sol Ring\n", encoding="utf-8")

    eval_runs_dir = tmp_path / "eval_runs"
    monkeypatch.setattr(run_eval_module, "EVAL_RUNS_DIR", eval_runs_dir)

    fake_analysis = {
        "estrategia_detectada": "ramp",
        "arquetipo": "artifacts",
        "puntos_fuertes": [],
        "problemas": [],
        "cortes_sugeridos": [],
        "añadidos_sugeridos": [],
    }
    fake_client = MagicMock()
    fake_client.messages.create.return_value = _fake_analysis_tool_use_message(fake_analysis)
    monkeypatch.setattr(run_eval_module.llm, "get_client", lambda: fake_client)

    exit_code = run_eval_module.main(["--deck", str(deck_path), "--db", str(db_path)])

    assert exit_code == 0
    saved_files = list((eval_runs_dir / "deck").glob("*.json"))
    assert len(saved_files) == 1
    record = json.loads(saved_files[0].read_text(encoding="utf-8"))
    assert record["deck"] == "deck.txt"
    assert record["raw_analysis"] == fake_analysis
    assert record["validated_analysis"] == fake_analysis
    assert record["params"]["style"] == "casual"


def test_run_eval_returns_one_when_no_sample_decks_found(tmp_path, monkeypatch):
    monkeypatch.setattr(run_eval_module, "SAMPLE_DECKS_DIR", tmp_path / "empty")
    monkeypatch.setattr(run_eval_module.llm, "get_client", lambda: MagicMock())

    exit_code = run_eval_module.main([])

    assert exit_code == 1
