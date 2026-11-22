import sqlite3

from analyzer import combos as combos_module


def make_db() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    combos_module.ensure_combo_cache_table(conn)
    return conn


class FakeResponse:
    def __init__(self, data: dict):
        self._data = data

    def raise_for_status(self):
        pass

    def json(self):
        return self._data


def fake_combo_response(card_names: list[str], produces: list[str], description: str = "") -> dict:
    return {
        "results": {
            "included": [
                {
                    "uses": [{"card": {"name": name}} for name in card_names],
                    "produces": [{"feature": {"name": p}} for p in produces],
                    "description": description,
                }
            ]
        }
    }


def test_find_combos_parses_included_results(monkeypatch):
    conn = make_db()
    monkeypatch.setattr(
        combos_module.requests,
        "post",
        lambda *a, **k: FakeResponse(
            fake_combo_response(
                ["Thassa's Oracle", "Demonic Consultation"], ["Win the game"], "Exile library, win."
            )
        ),
    )

    result = combos_module.find_combos(conn, ["Thassa's Oracle", "Demonic Consultation"], [])

    assert result == [
        {
            "cartas": ["Thassa's Oracle", "Demonic Consultation"],
            "produce": ["Win the game"],
            "descripcion": "Exile library, win.",
        }
    ]


def test_find_combos_uses_cache_without_calling_spellbook(monkeypatch):
    conn = make_db()
    monkeypatch.setattr(
        combos_module.requests,
        "post",
        lambda *a, **k: FakeResponse(fake_combo_response(["A", "B"], ["Win the game"])),
    )
    combos_module.find_combos(conn, ["A", "B"], [])

    monkeypatch.setattr(
        combos_module.requests,
        "post",
        lambda *a, **k: (_ for _ in ()).throw(AssertionError("no debería llamar de nuevo")),
    )
    result = combos_module.find_combos(conn, ["A", "B"], [])

    assert result == [{"cartas": ["A", "B"], "produce": ["Win the game"], "descripcion": ""}]


def test_find_combos_returns_empty_list_when_spellbook_is_unreachable(monkeypatch):
    conn = make_db()

    def raise_error(*a, **k):
        raise combos_module.requests.RequestException("timeout")

    monkeypatch.setattr(combos_module.requests, "post", raise_error)

    assert combos_module.find_combos(conn, ["A", "B"], []) == []


def test_find_combos_returns_empty_list_when_nothing_found(monkeypatch):
    conn = make_db()
    monkeypatch.setattr(
        combos_module.requests, "post", lambda *a, **k: FakeResponse({"results": {"included": []}})
    )

    assert combos_module.find_combos(conn, ["Sol Ring"], []) == []


def test_deck_hash_is_order_independent():
    assert combos_module._deck_hash(["A", "B"], []) == combos_module._deck_hash(["B", "A"], [])
