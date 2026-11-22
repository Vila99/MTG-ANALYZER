import json
import sqlite3

from analyzer.cards import Card
from analyzer.synergy import (
    build_candidate_pool,
    find_candidates_by_keywords,
    get_synergy_keywords,
)


def make_test_db() -> sqlite3.Connection:
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
    rows = [
        # (name, oracle_text, color_identity, legal)
        ("Token Maker", "Create a 1/1 white Soldier creature token.", ["W"], True),
        (
            "Token Enchantment Payoff",
            "Whenever you create a token, draw a card. Enchantment matters too.",
            ["W"],
            True,
        ),
        ("Unrelated Card", "Destroy target creature.", ["W"], True),
        ("Wrong Colors", "Create a token. Enchantment synergy.", ["U"], True),
        ("Banned Card", "Create a token.", ["W"], False),
        ("Sol Ring", "{T}: Add {C}{C}.", [], True),
    ]
    for i, (name, oracle_text, color_identity, legal) in enumerate(rows):
        conn.execute(
            "INSERT INTO cards VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (
                str(i),
                name,
                name.lower(),
                "",
                1.0,
                "Creature",
                oracle_text,
                json.dumps(color_identity),
                json.dumps(color_identity),
                json.dumps([]),
                json.dumps({"commander": "legal" if legal else "not_legal"}),
            ),
        )
    conn.commit()
    return conn


def make_commander(name: str = "Commander", oracle_text: str = "", color_identity=None) -> Card:
    return Card(
        name=name,
        mana_cost="{2}{W}",
        cmc=3.0,
        type_line="Legendary Creature",
        oracle_text=oracle_text,
        colors=color_identity or ["W"],
        color_identity=color_identity or ["W"],
        produced_mana=[],
        legalities={"commander": "legal"},
    )


def test_get_synergy_keywords_returns_empty_list_without_cache_or_llm():
    conn = make_test_db()
    assert get_synergy_keywords(conn, make_commander()) == []


def test_get_synergy_keywords_calls_llm_and_caches_result():
    conn = make_test_db()
    commander = make_commander()
    calls = []

    def fake_extract(card):
        calls.append(card.name)
        return ["token", "enchantment"]

    first = get_synergy_keywords(conn, commander, llm_extract=fake_extract)
    second = get_synergy_keywords(conn, commander, llm_extract=fake_extract)

    assert first == ["token", "enchantment"]
    assert second == ["token", "enchantment"]
    assert calls == ["Commander"]  # la segunda llamada usó la caché, no volvió a invocar al extractor


def test_find_candidates_by_keywords_matches_case_insensitively_and_filters_color_identity():
    conn = make_test_db()

    candidates = find_candidates_by_keywords(
        conn, keywords=["TOKEN"], color_identity=["W"], exclude_names=set()
    )

    names = {c.name for c in candidates}
    assert "Token Maker" in names
    assert "Wrong Colors" not in names  # fuera de la identidad de color
    assert "Banned Card" not in names  # no legal en commander
    assert "Unrelated Card" not in names  # no menciona la keyword


def test_find_candidates_by_keywords_excludes_given_names():
    conn = make_test_db()

    candidates = find_candidates_by_keywords(
        conn, keywords=["token"], color_identity=["W"], exclude_names={"Token Maker"}
    )

    assert "Token Maker" not in {c.name for c in candidates}


def test_find_candidates_by_keywords_ranks_by_number_of_matched_keywords():
    conn = make_test_db()

    candidates = find_candidates_by_keywords(
        conn, keywords=["token", "enchantment"], color_identity=["W"], exclude_names=set()
    )

    # "Token Enchantment Payoff" menciona las dos keywords; debe ir primero.
    assert candidates[0].name == "Token Enchantment Payoff"


def test_find_candidates_by_keywords_returns_empty_list_without_keywords():
    conn = make_test_db()
    assert find_candidates_by_keywords(conn, [], ["W"], set()) == []


def test_build_candidate_pool_uses_extractor_and_excludes_deck_cards():
    conn = make_test_db()
    commander = make_commander(color_identity=["W"])
    deck_card = Card(
        name="Token Enchantment Payoff",
        mana_cost="",
        cmc=1.0,
        type_line="Creature",
        oracle_text="Whenever you create a token, draw a card.",
        colors=["W"],
        color_identity=["W"],
        produced_mana=[],
        legalities={"commander": "legal"},
    )

    pool = build_candidate_pool(
        conn,
        [commander],
        [deck_card],
        llm_extract=lambda c: ["token"],
    )

    names = {c.name for c in pool}
    assert "Token Maker" in names
    assert "Token Enchantment Payoff" not in names  # ya está en el deck


def test_build_candidate_pool_returns_empty_list_without_commanders():
    conn = make_test_db()
    assert build_candidate_pool(conn, [], [], llm_extract=lambda c: ["token"]) == []
