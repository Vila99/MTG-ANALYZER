import json
import sqlite3

from analyzer.bracket import (
    classify_combo_speed,
    compute_floor,
    find_extra_turn_cards,
    find_game_changers,
    find_mass_land_destruction_candidates,
)
from analyzer.cards import Card


def make_card(name: str, oracle_text: str = "", type_line: str = "Sorcery") -> Card:
    return Card(
        name=name,
        mana_cost="",
        cmc=1.0,
        type_line=type_line,
        oracle_text=oracle_text,
        colors=[],
        color_identity=[],
        produced_mana=[],
        legalities={"commander": "legal"},
    )


GAME_CHANGERS = frozenset({"rhystic study", "smothering tithe", "cyclonic rift"})


def test_find_game_changers_matches_deck_and_commander():
    commanders = [make_card("Narset, Parter of Veils")]
    deck = [make_card("Rhystic Study"), make_card("Sol Ring"), make_card("Smothering Tithe")]
    found = find_game_changers(commanders, deck, GAME_CHANGERS)
    assert set(found) == {"Rhystic Study", "Smothering Tithe"}


def test_find_game_changers_no_duplicates():
    deck = [make_card("Rhystic Study"), make_card("Rhystic Study")]
    found = find_game_changers([], deck, GAME_CHANGERS)
    assert found == ["Rhystic Study"]


def test_find_mass_land_destruction_candidates():
    deck = [
        make_card("Armageddon", oracle_text="Destroy all lands."),
        make_card("Winter Orb", oracle_text="Artifacts and lands don't untap during their controllers' untap steps."),
        make_card("Sol Ring", oracle_text="{T}: Add {C}{C}."),
    ]
    found = find_mass_land_destruction_candidates(deck)
    assert set(found) == {"Armageddon", "Winter Orb"}


def test_find_extra_turn_cards():
    deck = [
        make_card("Time Warp", oracle_text="Target player takes an extra turn after this one."),
        make_card("Sol Ring", oracle_text="{T}: Add {C}{C}."),
    ]
    found = find_extra_turn_cards(deck)
    assert found == ["Time Warp"]


def test_compute_floor_defaults_to_one_with_no_signals():
    result = compute_floor([], [make_card("Sol Ring")])
    assert result["floor"] == 1
    assert result["razones_suelo"] == []


def test_compute_floor_one_to_three_game_changers_means_bracket_three():
    deck = [make_card("Rhystic Study"), make_card("Smothering Tithe")]
    result = compute_floor([], deck)
    assert result["floor"] == 3
    assert result["game_changers"] == ["Rhystic Study", "Smothering Tithe"]


def test_compute_floor_four_or_more_game_changers_means_bracket_four():
    # Las cuatro son Game Changers reales (data/game_changers.json); compute_floor
    # carga la lista real cuando no se le pasa una explícita.
    deck = [
        make_card("Rhystic Study"),
        make_card("Smothering Tithe"),
        make_card("Cyclonic Rift"),
        make_card("Mana Vault"),
    ]
    result = compute_floor([], deck)
    assert result["floor"] == 4
    assert len(result["game_changers"]) == 4


def test_compute_floor_mass_land_destruction_forces_bracket_four():
    deck = [make_card("Armageddon", oracle_text="Destroy all lands.")]
    result = compute_floor([], deck)
    assert result["floor"] == 4
    assert "Armageddon" in result["destruccion_tierras_candidatas"]


def test_compute_floor_single_extra_turn_card_forces_bracket_two():
    deck = [make_card("Time Warp", oracle_text="Target player takes an extra turn after this one.")]
    result = compute_floor([], deck)
    assert result["floor"] == 2


def test_compute_floor_multiple_extra_turn_cards_forces_bracket_four():
    deck = [
        make_card("Time Warp", oracle_text="Target player takes an extra turn after this one."),
        make_card("Temporal Manipulation", oracle_text="Take an extra turn after this one."),
    ]
    result = compute_floor([], deck)
    assert result["floor"] == 4


def test_compute_floor_takes_the_highest_signal():
    deck = [
        make_card("Time Warp", oracle_text="Target player takes an extra turn after this one."),
        make_card("Armageddon", oracle_text="Destroy all lands."),
    ]
    result = compute_floor([], deck)
    assert result["floor"] == 4
    assert len(result["razones_suelo"]) == 2


def make_combo_db() -> sqlite3.Connection:
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
    for i, (name, cmc) in enumerate([("Barata Uno", 1.0), ("Barata Dos", 2.0), ("Cara", 6.0)]):
        conn.execute(
            "INSERT INTO cards VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (
                str(i), name, name.lower(), "", cmc, "Artifact", "",
                json.dumps([]), json.dumps([]), json.dumps([]), json.dumps({"commander": "legal"}),
            ),
        )
    conn.commit()
    return conn


def test_classify_combo_speed_temprano_when_cheap():
    conn = make_combo_db()
    combo = {"cartas": ["Barata Uno", "Barata Dos"]}  # cmc total 3
    assert classify_combo_speed(conn, combo) == "temprano"


def test_classify_combo_speed_tardio_when_expensive():
    conn = make_combo_db()
    combo = {"cartas": ["Cara", "Barata Dos"]}  # cmc total 8
    assert classify_combo_speed(conn, combo) == "tardío"


def test_compute_floor_cheap_combo_forces_bracket_four():
    conn = make_combo_db()
    combo = {"cartas": ["Barata Uno", "Barata Dos"], "produce": ["Win the game"], "descripcion": ""}
    result = compute_floor([], [make_card("Sol Ring")], conn, [combo])
    assert result["floor"] == 4
    assert result["combos"][0]["velocidad"] == "temprano"


def test_compute_floor_expensive_combo_forces_bracket_three():
    conn = make_combo_db()
    combo = {"cartas": ["Cara", "Barata Dos"], "produce": ["Win the game"], "descripcion": ""}
    result = compute_floor([], [make_card("Sol Ring")], conn, [combo])
    assert result["floor"] == 3
    assert result["combos"][0]["velocidad"] == "tardío"


def test_compute_floor_without_combos_or_conn_omits_combo_signal():
    result = compute_floor([], [make_card("Sol Ring")])
    assert result["combos"] == []
