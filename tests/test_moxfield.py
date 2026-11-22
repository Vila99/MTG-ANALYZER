import pytest

from analyzer import moxfield as moxfield_module
from analyzer.moxfield import extract_deck_id, fetch_moxfield_deck


class FakeResponse:
    def __init__(self, status_code: int = 200, data: dict | None = None):
        self.status_code = status_code
        self.ok = status_code < 400
        self._data = data

    def json(self):
        return self._data

    def raise_for_status(self):
        pass


@pytest.mark.parametrize(
    "value,expected",
    [
        ("https://www.moxfield.com/decks/abc123XYZ", "abc123XYZ"),
        ("https://moxfield.com/decks/abc123XYZ/", "abc123XYZ"),
        ("https://moxfield.com/decks/abc123XYZ?utm=foo", "abc123XYZ"),
        ("abc123XYZ", "abc123XYZ"),
    ],
)
def test_extract_deck_id(value, expected):
    assert extract_deck_id(value) == expected


def test_fetch_moxfield_deck_parses_commanders_and_mainboard(monkeypatch):
    monkeypatch.setattr(
        moxfield_module.requests,
        "get",
        lambda *a, **k: FakeResponse(
            200,
            {
                "commanders": {"Atraxa, Praetors' Voice": {"quantity": 1}},
                "mainboard": {
                    "Sol Ring": {"quantity": 1},
                    "Forest": {"quantity": 35},
                },
            },
        ),
    )

    parsed = fetch_moxfield_deck("https://www.moxfield.com/decks/abc123")

    assert parsed.commanders == ["Atraxa, Praetors' Voice"]
    names_and_qty = {(entry.name, entry.quantity) for entry in parsed.cards}
    assert names_and_qty == {("Sol Ring", 1), ("Forest", 35)}


def test_fetch_moxfield_deck_raises_on_404(monkeypatch):
    monkeypatch.setattr(moxfield_module.requests, "get", lambda *a, **k: FakeResponse(404))

    with pytest.raises(ValueError, match="se encontró"):
        fetch_moxfield_deck("https://www.moxfield.com/decks/no-existe")


def test_fetch_moxfield_deck_raises_on_server_error(monkeypatch):
    monkeypatch.setattr(moxfield_module.requests, "get", lambda *a, **k: FakeResponse(500))

    with pytest.raises(ValueError):
        fetch_moxfield_deck("https://www.moxfield.com/decks/abc123")


def test_fetch_moxfield_deck_raises_on_empty_deck(monkeypatch):
    monkeypatch.setattr(
        moxfield_module.requests,
        "get",
        lambda *a, **k: FakeResponse(200, {"commanders": {}, "mainboard": {}}),
    )

    with pytest.raises(ValueError):
        fetch_moxfield_deck("https://www.moxfield.com/decks/vacio")


def test_fetch_moxfield_deck_raises_on_blank_input():
    with pytest.raises(ValueError):
        fetch_moxfield_deck("   ")
