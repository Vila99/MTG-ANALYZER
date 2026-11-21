from unittest.mock import MagicMock

import pytest

from analyzer.cards import Card
from analyzer.llm import classify_card_with_haiku, get_client


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
