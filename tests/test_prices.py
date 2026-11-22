import sqlite3
from datetime import datetime, timedelta, timezone

from analyzer import prices as prices_module


def make_db() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    prices_module.ensure_price_cache_table(conn)
    return conn


class FakeResponse:
    def __init__(self, data: dict):
        self._data = data

    def raise_for_status(self):
        pass

    def json(self):
        return self._data


def test_fetch_prices_uses_cache_without_calling_scryfall(monkeypatch):
    conn = make_db()
    prices_module._cache_price(conn, "Sol Ring", 0.85)
    conn.commit()

    calls = []
    monkeypatch.setattr(prices_module.requests, "post", lambda *a, **k: calls.append(1) or FakeResponse({}))

    result = prices_module.fetch_prices(conn, ["Sol Ring"])

    assert result == {"Sol Ring": 0.85}
    assert calls == []


def test_fetch_prices_calls_scryfall_for_uncached_names_and_caches_result(monkeypatch):
    conn = make_db()
    monkeypatch.setattr(
        prices_module.requests,
        "post",
        lambda *a, **k: FakeResponse(
            {"data": [{"name": "Smothering Tithe", "prices": {"eur": "41.95"}}]}
        ),
    )

    result = prices_module.fetch_prices(conn, ["Smothering Tithe"])

    assert result == {"Smothering Tithe": 41.95}
    # segunda llamada: ya en caché, no debería volver a pedirlo
    monkeypatch.setattr(
        prices_module.requests, "post", lambda *a, **k: (_ for _ in ()).throw(AssertionError("no cache"))
    )
    assert prices_module.fetch_prices(conn, ["Smothering Tithe"]) == {"Smothering Tithe": 41.95}


def test_fetch_prices_returns_none_for_card_without_eur_price(monkeypatch):
    conn = make_db()
    monkeypatch.setattr(
        prices_module.requests,
        "post",
        lambda *a, **k: FakeResponse({"data": [{"name": "Some Card", "prices": {"eur": None}}]}),
    )

    result = prices_module.fetch_prices(conn, ["Some Card"])

    assert result == {"Some Card": None}


def test_fetch_prices_returns_none_for_name_not_found(monkeypatch):
    conn = make_db()
    monkeypatch.setattr(
        prices_module.requests,
        "post",
        lambda *a, **k: FakeResponse({"data": [], "not_found": [{"name": "Nombre Falso"}]}),
    )

    result = prices_module.fetch_prices(conn, ["Nombre Falso"])

    assert result == {"Nombre Falso": None}


def test_fetch_prices_batches_in_groups_of_75(monkeypatch):
    conn = make_db()
    calls = []

    def fake_post(url, json, headers, timeout):
        calls.append(len(json["identifiers"]))
        return FakeResponse(
            {"data": [{"name": ident["name"], "prices": {"eur": "1.00"}} for ident in json["identifiers"]]}
        )

    monkeypatch.setattr(prices_module.requests, "post", fake_post)

    names = [f"Card {i}" for i in range(100)]
    result = prices_module.fetch_prices(conn, names)

    assert calls == [75, 25]
    assert len(result) == 100


def test_fetch_prices_refetches_when_cache_expired(monkeypatch):
    conn = make_db()
    old = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
    conn.execute(
        "INSERT INTO card_prices (name_normalized, name, eur, fetched_at) VALUES (?, ?, ?, ?)",
        ("sol ring", "Sol Ring", 0.5, old),
    )
    conn.commit()

    monkeypatch.setattr(
        prices_module.requests,
        "post",
        lambda *a, **k: FakeResponse({"data": [{"name": "Sol Ring", "prices": {"eur": "0.85"}}]}),
    )

    result = prices_module.fetch_prices(conn, ["Sol Ring"], max_age_days=7)

    assert result == {"Sol Ring": 0.85}
