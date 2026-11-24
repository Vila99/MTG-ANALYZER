from analyzer.budget import annotate_prices


def make_candidata(carta, **kwargs):
    return {"carta": carta, "rol": "ramp", "motivo": "motivo", **kwargs}


def make_analysis(problemas):
    return {"problemas": problemas}


def test_annotate_prices_attaches_price_regardless_of_mode(monkeypatch):
    import analyzer.budget as budget_module

    monkeypatch.setattr(
        budget_module.prices_module, "fetch_prices", lambda conn, names: {name: 1.5 for name in names}
    )
    analysis = make_analysis(
        [{"categoria": "Ramp", "severidad": "media", "explicacion": "...", "candidatas_sugeridas": [make_candidata("X")]}]
    )

    result = annotate_prices(conn=None, analysis=analysis, budget_mode=None)

    assert result["problemas"][0]["candidatas_sugeridas"][0]["precio_eur"] == 1.5


def test_annotate_prices_returns_unchanged_without_problemas():
    analysis = {"problemas": []}
    assert annotate_prices(conn=None, analysis=analysis, budget_mode=None) == analysis


def test_annotate_prices_does_not_reorder_in_libre_mode(monkeypatch):
    import analyzer.budget as budget_module

    monkeypatch.setattr(
        budget_module.prices_module,
        "fetch_prices",
        lambda conn, names: {"Cara": 50.0, "Barata": 2.0}.copy(),
    )
    analysis = make_analysis(
        [
            {
                "categoria": "Ramp",
                "severidad": "media",
                "explicacion": "...",
                "candidatas_sugeridas": [make_candidata("Cara"), make_candidata("Barata")],
            }
        ]
    )

    result = annotate_prices(conn=None, analysis=analysis, budget_mode="libre")

    cartas = [c["carta"] for c in result["problemas"][0]["candidatas_sugeridas"]]
    assert cartas == ["Cara", "Barata"]


def test_annotate_prices_sorts_cheapest_first_in_ajustado_mode(monkeypatch):
    import analyzer.budget as budget_module

    monkeypatch.setattr(
        budget_module.prices_module,
        "fetch_prices",
        lambda conn, names: {"Cara": 50.0, "Barata": 2.0}.copy(),
    )
    analysis = make_analysis(
        [
            {
                "categoria": "Ramp",
                "severidad": "media",
                "explicacion": "...",
                "candidatas_sugeridas": [make_candidata("Cara"), make_candidata("Barata")],
            }
        ]
    )

    result = annotate_prices(conn=None, analysis=analysis, budget_mode="ajustado")

    cartas = [c["carta"] for c in result["problemas"][0]["candidatas_sugeridas"]]
    assert cartas == ["Barata", "Cara"]


def test_annotate_prices_puts_unknown_price_last_in_ajustado_mode(monkeypatch):
    import analyzer.budget as budget_module

    monkeypatch.setattr(
        budget_module.prices_module, "fetch_prices", lambda conn, names: {"Barata": 2.0}
    )
    analysis = make_analysis(
        [
            {
                "categoria": "Ramp",
                "severidad": "media",
                "explicacion": "...",
                "candidatas_sugeridas": [make_candidata("Sin precio"), make_candidata("Barata")],
            }
        ]
    )

    result = annotate_prices(conn=None, analysis=analysis, budget_mode="ajustado")

    cartas = [c["carta"] for c in result["problemas"][0]["candidatas_sugeridas"]]
    assert cartas == ["Barata", "Sin precio"]
