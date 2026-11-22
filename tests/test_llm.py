from unittest.mock import MagicMock

import pytest

from analyzer.cards import Card
from analyzer.llm import (
    analyze_deck,
    build_analysis_payload,
    classify_card_with_haiku,
    get_client,
    load_system_prompt,
)


def make_card(name: str = "Mystery Card") -> Card:
    return Card(
        name=name,
        mana_cost="{2}{U}",
        cmc=3.0,
        type_line="Creature",
        oracle_text="Whenever you draw a card, put a +1/+1 counter on this creature.",
        colors=["U"],
        color_identity=["U"],
        produced_mana=[],
        legalities={"commander": "legal"},
    )


def _fake_tool_use_message(roles: list[str]):
    block = MagicMock()
    block.type = "tool_use"
    block.name = "classify_card"
    block.input = {"roles": roles}
    message = MagicMock()
    message.content = [block]
    return message


def test_classify_card_with_haiku_parses_tool_use_response():
    client = MagicMock()
    client.messages.create.return_value = _fake_tool_use_message(["synergy", "draw"])

    roles = classify_card_with_haiku(client, make_card())

    assert roles == ["synergy", "draw"]
    client.messages.create.assert_called_once()
    _, kwargs = client.messages.create.call_args
    assert kwargs["tool_choice"] == {"type": "tool", "name": "classify_card"}


def test_classify_card_with_haiku_filters_invalid_roles():
    client = MagicMock()
    client.messages.create.return_value = _fake_tool_use_message(["draw", "not_a_real_role"])

    roles = classify_card_with_haiku(client, make_card())

    assert roles == ["draw"]


def test_classify_card_with_haiku_defaults_to_other_without_tool_use():
    client = MagicMock()
    message = MagicMock()
    message.content = []
    client.messages.create.return_value = message

    roles = classify_card_with_haiku(client, make_card())

    assert roles == ["other"]


def test_get_client_requires_api_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(RuntimeError):
        get_client()


def test_load_system_prompt_includes_the_deckbuilding_knowledge():
    prompt = load_system_prompt()
    # El contrato de system_analysis.md
    assert "analyze_deck" in prompt
    # El marco de criterios de prompts/knowledge/deckbuilding.md
    assert "generador" in prompt
    assert "goldfish" in prompt


def make_commander() -> Card:
    return Card(
        name="Atraxa, Praetors' Voice",
        mana_cost="{G}{W}{U}{B}",
        cmc=4.0,
        type_line="Legendary Creature — Phyrexian Angel",
        oracle_text="Flying, vigilance, deathtouch, lifelink.",
        colors=["W", "U", "B", "G"],
        color_identity=["W", "U", "B", "G"],
        produced_mana=[],
        legalities={"commander": "legal"},
    )


def make_deck_card(name: str, oracle_text: str = "") -> Card:
    return Card(
        name=name,
        mana_cost="{1}",
        cmc=1.0,
        type_line="Artifact",
        oracle_text=oracle_text,
        colors=[],
        color_identity=[],
        produced_mana=[],
        legalities={"commander": "legal"},
    )


def test_build_analysis_payload_groups_duplicates_and_includes_roles():
    commander = make_commander()
    sol_ring = make_deck_card("Sol Ring", "{T}: Add {C}{C}.")
    forest = make_deck_card("Forest")
    deck_cards = [sol_ring, forest, forest, forest]
    card_roles = {"Sol Ring": ["ramp"], "Forest": ["land"]}

    payload = build_analysis_payload(
        [commander], deck_cards, card_roles, params={"bracket": 3}
    )

    assert payload["comandantes"] == [
        {
            "nombre": "Atraxa, Praetors' Voice",
            "identidad_color": ["W", "U", "B", "G"],
            "texto_oracle": commander.oracle_text,
        }
    ]
    assert payload["metricas"]["tamano_deck"] == 5  # 4 cartas + 1 comandante
    cartas_by_name = {c["nombre"]: c for c in payload["cartas"]}
    assert cartas_by_name["Forest"]["cantidad"] == 3
    assert cartas_by_name["Forest"]["roles"] == ["land"]
    assert cartas_by_name["Sol Ring"]["roles"] == ["ramp"]
    assert payload["parametros_usuario"] == {"bracket": 3}
    assert payload["pool_candidatas"] == []


def test_build_analysis_payload_includes_candidate_pool():
    commander = make_commander()
    payload = build_analysis_payload(
        [commander],
        [],
        {},
        params={},
        candidate_pool=[make_deck_card("Arcane Signet", "Add one mana of any color.")],
    )
    assert payload["pool_candidatas"] == [
        {"nombre": "Arcane Signet", "texto_oracle": "Add one mana of any color."}
    ]


def _fake_analysis_tool_use_message(analysis: dict):
    block = MagicMock()
    block.type = "tool_use"
    block.name = "analyze_deck"
    block.input = analysis
    message = MagicMock()
    message.content = [block]
    return message


def test_analyze_deck_returns_tool_input():
    fake_analysis = {
        "estrategia_detectada": "superfriends",
        "arquetipo": "planeswalkers",
        "puntos_fuertes": ["buena ventaja de cartas"],
        "problemas": [],
        "cortes_sugeridos": [],
        "añadidos_sugeridos": [],
    }
    client = MagicMock()
    client.messages.create.return_value = _fake_analysis_tool_use_message(fake_analysis)

    result = analyze_deck(client, {"comandantes": []})

    assert result == fake_analysis
    _, kwargs = client.messages.create.call_args
    assert kwargs["tool_choice"] == {"type": "tool", "name": "analyze_deck"}
    assert kwargs["system"][0]["cache_control"] == {"type": "ephemeral"}


def test_analyze_deck_raises_without_tool_use():
    client = MagicMock()
    message = MagicMock()
    message.content = []
    client.messages.create.return_value = message

    with pytest.raises(RuntimeError):
        analyze_deck(client, {"comandantes": []})
