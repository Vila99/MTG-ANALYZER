import random

from analyzer.cards import Card
from analyzer.goldfish import (
    SimCard,
    build_sim_deck,
    run_monte_carlo,
    simulate_one_game,
)


def make_card(name: str, cmc: float, is_land: bool, color_identity: list[str] | None = None) -> Card:
    return Card(
        name=name,
        mana_cost="",
        cmc=cmc,
        type_line="Basic Land" if is_land else "Artifact",
        oracle_text="",
        colors=color_identity or [],
        color_identity=color_identity or [],
        produced_mana=color_identity or [],
        legalities={"commander": "legal"},
    )


def make_commander(cmc: float, color_identity: list[str]) -> Card:
    return Card(
        name="Commander",
        mana_cost="",
        cmc=cmc,
        type_line="Legendary Creature",
        oracle_text="",
        colors=color_identity,
        color_identity=color_identity,
        produced_mana=[],
        legalities={"commander": "legal"},
    )


def test_build_sim_deck_tags_nonland_ramp_from_roles():
    rock = make_card("Sol Ring", cmc=1.0, is_land=False)
    forest = make_card("Forest", cmc=0.0, is_land=True, color_identity=["G"])
    sim_cards = build_sim_deck([rock, forest], {"Sol Ring": ["ramp"], "Forest": ["ramp", "land"]})

    by_name = {c.name: c for c in sim_cards}
    assert by_name["Sol Ring"].is_ramp is True
    # Una tierra nunca cuenta como "ramp" aunque el clasificador le ponga
    # ese rol: ya produce su maná normal, no es un extra.
    assert by_name["Forest"].is_ramp is False


def test_simulate_one_game_without_lands_never_gets_mana():
    deck = [SimCard(name="Spell", cmc=2.0, is_land=False, is_ramp=False, produced_mana=()) for _ in range(40)]
    rng = random.Random(1)

    result = simulate_one_game(deck, commander_identity=set(), commander_cmc=3.0, rng=rng, turns=6)

    assert result.mana_por_turno == (0, 0, 0, 0, 0, 0)
    assert result.tierras_turno_3 == 0
    assert result.comandante_turno is None


def test_simulate_one_game_all_lands_plays_one_per_turn_and_forces_mulligan():
    deck = [SimCard(name=f"Land{i}", cmc=0.0, is_land=True, is_ramp=False, produced_mana=("G",)) for i in range(40)]
    rng = random.Random(1)

    result = simulate_one_game(deck, commander_identity=set(), commander_cmc=0.0, rng=rng, turns=8)

    assert result.mana_por_turno == tuple(range(1, 9))
    # Mano inicial de 7 tierras siempre dispara el mulligan simplificado
    # (demasiadas tierras), y se agota el máximo de 2 intentos.
    assert result.mulligans == 2


def test_simulate_one_game_commander_castable_once_mana_and_colors_available():
    land = SimCard(name="Forest", cmc=0.0, is_land=True, is_ramp=False, produced_mana=("G",))
    deck = [land] * 40
    rng = random.Random(1)

    result = simulate_one_game(
        deck, commander_identity={"G"}, commander_cmc=3.0, rng=rng, turns=6
    )

    assert result.comandante_turno == 3  # 3 tierras de G en juego para el turno 3


def test_simulate_one_game_commander_never_castable_without_the_right_color():
    land = SimCard(name="Island", cmc=0.0, is_land=True, is_ramp=False, produced_mana=("U",))
    deck = [land] * 40
    rng = random.Random(1)

    result = simulate_one_game(
        deck, commander_identity={"G"}, commander_cmc=1.0, rng=rng, turns=6
    )

    assert result.comandante_turno is None


def test_run_monte_carlo_is_reproducible_with_seed():
    deck_cards = [make_card(f"Land{i}", cmc=0.0, is_land=True, color_identity=["G"]) for i in range(40)]
    deck_cards += [make_card(f"Rock{i}", cmc=2.0, is_land=False) for i in range(10)]
    commanders = [make_commander(cmc=3.0, color_identity=["G"])]
    card_roles = {f"Rock{i}": ["ramp"] for i in range(10)}

    first = run_monte_carlo(deck_cards, card_roles, commanders, n_sims=200, seed=42)
    second = run_monte_carlo(deck_cards, card_roles, commanders, n_sims=200, seed=42)

    assert first == second


def test_run_monte_carlo_omits_colores_for_colorless_commander():
    deck_cards = [make_card(f"Land{i}", cmc=0.0, is_land=True) for i in range(40)]
    commanders = [make_commander(cmc=2.0, color_identity=[])]

    stats = run_monte_carlo(deck_cards, {}, commanders, n_sims=50, seed=1)

    assert "colores_disponibles_turno_4" not in stats


def test_run_monte_carlo_includes_colores_for_colored_commander():
    deck_cards = [make_card(f"Land{i}", cmc=0.0, is_land=True, color_identity=["G"]) for i in range(40)]
    commanders = [make_commander(cmc=2.0, color_identity=["G"])]

    stats = run_monte_carlo(deck_cards, {}, commanders, n_sims=50, seed=1)

    assert "colores_disponibles_turno_4" in stats
    assert stats["colores_disponibles_turno_4"]["G"] > 0.0


def test_run_monte_carlo_rejects_nonpositive_n_sims():
    import pytest

    deck_cards = [make_card("Land", cmc=0.0, is_land=True)]
    commanders = [make_commander(cmc=1.0, color_identity=[])]
    with pytest.raises(ValueError):
        run_monte_carlo(deck_cards, {}, commanders, n_sims=0, seed=1)
