import sqlite3

from analyzer.cards import Card
from analyzer.roles import classify_by_rules, classify_card, get_cached_roles


def make_card(name: str, oracle_text: str = "", type_line: str = "Creature") -> Card:
    return Card(
        name=name,
        mana_cost="",
        cmc=0.0,
        type_line=type_line,
        oracle_text=oracle_text,
        colors=[],
        color_identity=[],
        produced_mana=[],
        legalities={"commander": "legal"},
    )


def make_db() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    return conn


def test_land_type_is_tagged_land():
    card = make_card("Forest", type_line="Basic Land — Forest")
    assert "land" in classify_by_rules(card)


def test_ramp_pattern_mana_rock():
    card = make_card("Sol Ring", oracle_text="{T}: Add {C}{C}.", type_line="Artifact")
    assert "ramp" in classify_by_rules(card)


def test_ramp_pattern_land_tutor():
    card = make_card(
        "Rampant Growth",
        oracle_text="Search your library for a basic land card, put it onto the battlefield tapped, then shuffle.",
        type_line="Sorcery",
    )
    assert "ramp" in classify_by_rules(card)


def test_draw_pattern():
    card = make_card("Sign in Blood", oracle_text="Target player draws two cards.", type_line="Sorcery")
    assert "draw" in classify_by_rules(card)


def test_wipe_pattern_takes_priority_over_removal():
    card = make_card(
        "Wrath of God", oracle_text="Destroy all creatures. They can't be regenerated.", type_line="Sorcery"
    )
    roles = classify_by_rules(card)
    assert "wipe" in roles
    assert "removal" not in roles


def test_removal_pattern():
    card = make_card("Swords to Plowshares", oracle_text="Exile target creature.", type_line="Instant")
    assert "removal" in classify_by_rules(card)


def test_protection_pattern():
    card = make_card("Swiftfoot Boots", oracle_text="Equipped creature has hexproof and haste.", type_line="Artifact")
    assert "protection" in classify_by_rules(card)


def test_tutor_pattern_generic_not_ramp():
    card = make_card(
        "Vampiric Tutor", oracle_text="Search your library for a card and put it on top.", type_line="Instant"
    )
    roles = classify_by_rules(card)
    assert "tutor" in roles
    assert "ramp" not in roles


def test_ramp_pattern_plain_english_mana_rock():
    card = make_card(
        "Arcane Signet",
        oracle_text="{T}: Add one mana of any color in your commander's color identity.",
        type_line="Artifact",
    )
    assert "ramp" in classify_by_rules(card)


def test_plain_english_mana_ability_on_land_is_not_ramp():
    card = make_card(
        "Command Tower",
        oracle_text="{T}: Add one mana of any color in your commander's color identity.",
        type_line="Land",
    )
    roles = classify_by_rules(card)
    assert "land" in roles
    assert "ramp" not in roles


def test_wipe_pattern_with_literal_x_power_toughness():
    card = make_card(
        "Toxic Deluge",
        oracle_text="As an additional cost to cast this spell, pay X life.\nAll creatures get -X/-X until end of turn.",
        type_line="Sorcery",
    )
    assert "wipe" in classify_by_rules(card)


def test_removal_pattern_bounce_to_hand():
    card = make_card(
        "Cyclonic Rift",
        oracle_text="Return target nonland permanent you don't control to its owner's hand.",
        type_line="Instant",
    )
    assert "removal" in classify_by_rules(card)


def test_no_rule_matches_returns_empty_list():
    card = make_card("Vanilla Bear", oracle_text="", type_line="Creature — Bear")
    assert classify_by_rules(card) == []


def test_classify_card_uses_cache_before_rules():
    conn = make_db()
    card = make_card("Sol Ring", oracle_text="{T}: Add {C}{C}.", type_line="Artifact")

    first = classify_card(conn, card)
    assert first == ["ramp"]
    assert get_cached_roles(conn, card) == ["ramp"]

    calls = []

    def fake_llm(c):
        calls.append(c)
        return ["other"]

    second = classify_card(conn, card, llm_classify=fake_llm)
    assert second == ["ramp"]
    assert calls == []  # no debería llamar al LLM si ya está en caché


def test_classify_card_falls_back_to_llm_when_rules_find_nothing():
    conn = make_db()
    card = make_card("Vanilla Bear", oracle_text="", type_line="Creature — Bear")

    def fake_llm(c):
        return ["synergy"]

    roles = classify_card(conn, card, llm_classify=fake_llm)
    assert roles == ["synergy"]
    assert get_cached_roles(conn, card) == ["synergy"]


def test_classify_card_without_llm_returns_other_and_does_not_cache():
    conn = make_db()
    card = make_card("Vanilla Bear", oracle_text="", type_line="Creature — Bear")

    roles = classify_card(conn, card, llm_classify=None)
    assert roles == ["other"]
    assert get_cached_roles(conn, card) is None
