from analyzer.cards import Card
from analyzer import metrics


def make_card(
    name: str,
    mana_cost: str = "",
    cmc: float = 0.0,
    type_line: str = "Creature",
    color_identity: list[str] | None = None,
    produced_mana: list[str] | None = None,
    legal: bool = True,
) -> Card:
    return Card(
        name=name,
        mana_cost=mana_cost,
        cmc=cmc,
        type_line=type_line,
        oracle_text="",
        colors=[],
        color_identity=color_identity or [],
        produced_mana=produced_mana or [],
        legalities={"commander": "legal" if legal else "not_legal"},
    )


def test_mana_curve_excludes_lands_and_groups_by_cmc():
    cards = [
        make_card("Sol Ring", cmc=1.0, type_line="Artifact"),
        make_card("Rhystic Study", cmc=3.0, type_line="Enchantment"),
        make_card("Cyclonic Rift", cmc=2.0, type_line="Instant"),
        make_card("Command Tower", cmc=0.0, type_line="Land"),
    ]
    assert metrics.mana_curve(cards) == {1: 1, 2: 1, 3: 1}


def test_average_cmc_excludes_lands():
    cards = [
        make_card("A", cmc=2.0, type_line="Creature"),
        make_card("B", cmc=4.0, type_line="Creature"),
        make_card("Forest", cmc=0.0, type_line="Basic Land"),
    ]
    assert metrics.average_cmc(cards) == 3.0


def test_average_cmc_with_no_nonland_cards_is_zero():
    cards = [make_card("Forest", cmc=0.0, type_line="Basic Land")]
    assert metrics.average_cmc(cards) == 0.0


def test_count_lands():
    cards = [
        make_card("Forest", type_line="Basic Land"),
        make_card("Island", type_line="Basic Land"),
        make_card("Sol Ring", type_line="Artifact"),
    ]
    assert metrics.count_lands(cards) == 2


def test_color_pips_counts_hybrid_for_both_colors():
    cards = [make_card("Example", mana_cost="{1}{W/U}{G}")]
    pips = metrics.color_pips(cards)
    assert pips["W"] == 1
    assert pips["U"] == 1
    assert pips["G"] == 1
    assert pips["B"] == 0
    assert pips["R"] == 0


def test_mana_sources_counts_produced_mana():
    cards = [
        make_card("Command Tower", type_line="Land", produced_mana=["W", "U", "B", "R", "G"]),
        make_card("Forest", type_line="Basic Land", produced_mana=["G"]),
    ]
    sources = metrics.mana_sources(cards)
    assert sources["G"] == 2
    assert sources["W"] == 1


def test_color_identity_violations():
    cards = [
        make_card("In Identity", color_identity=["W", "U"]),
        make_card("Out of Identity", color_identity=["R"]),
    ]
    violations = metrics.color_identity_violations(cards, {"W", "U", "B"})
    assert [c.name for c in violations] == ["Out of Identity"]


def test_illegal_cards():
    cards = [
        make_card("Legal Card", legal=True),
        make_card("Banned Card", legal=False),
    ]
    illegal = metrics.illegal_cards(cards)
    assert [c.name for c in illegal] == ["Banned Card"]
