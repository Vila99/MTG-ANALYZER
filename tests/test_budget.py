from analyzer.budget import apply_budget_to_analysis, select_within_budget


def make_addition(carta, categoria_problema=None, **kwargs):
    return {
        "carta": carta,
        "rol": "ramp",
        "reemplaza_a": None,
        "categoria_problema": categoria_problema,
        "motivo": "motivo",
        **kwargs,
    }


def test_select_within_budget_prioritizes_alta_severity_first():
    additions = [
        make_addition("Barata Media", categoria_problema="Ramp"),
        make_addition("Cara Alta", categoria_problema="Ventaja de mesa"),
    ]
    prices = {"Barata Media": 2.0, "Cara Alta": 50.0}
    severity = {"Ramp": "media", "Ventaja de mesa": "alta"}

    selection = select_within_budget(additions, prices, severity, budget=50.0, overage=0.0)

    by_name = {a["carta"]: a for a in selection.additions}
    assert by_name["Cara Alta"]["incluido"] is True
    assert by_name["Barata Media"]["incluido"] is False  # ya no cabe tras incluir la alta
    assert selection.coste_estimado == 50.0


def test_select_within_budget_excludes_once_overage_exceeded():
    additions = [make_addition("A"), make_addition("B"), make_addition("C")]
    prices = {"A": 10.0, "B": 10.0, "C": 10.0}

    selection = select_within_budget(additions, prices, {}, budget=15.0, overage=5.0)

    included = {a["carta"] for a in selection.additions if a["incluido"]}
    assert included == {"A", "B"}  # 20 <= 15+5; la tercera (30) ya no cabe
    assert selection.supera_presupuesto is True
    assert selection.diferencia == 5.0


def test_select_within_budget_always_includes_unknown_price_items():
    additions = [make_addition("Sin precio")]
    selection = select_within_budget(additions, {}, {}, budget=0.0, overage=0.0)

    assert selection.additions[0]["incluido"] is True
    assert selection.additions[0]["precio_eur"] is None
    assert selection.coste_estimado == 0.0


def test_select_within_budget_prefers_cheaper_option_within_same_severity():
    additions = [
        make_addition("Cara", categoria_problema="Ramp"),
        make_addition("Barata", categoria_problema="Ramp"),
    ]
    prices = {"Cara": 20.0, "Barata": 5.0}
    severity = {"Ramp": "media"}

    selection = select_within_budget(additions, prices, severity, budget=5.0, overage=0.0)

    by_name = {a["carta"]: a for a in selection.additions}
    assert by_name["Barata"]["incluido"] is True
    assert by_name["Cara"]["incluido"] is False


def test_apply_budget_to_analysis_returns_unchanged_when_budget_is_none():
    analysis = {"anadidos_sugeridos": [make_addition("X")], "problemas": []}
    assert apply_budget_to_analysis(conn=None, analysis=analysis, budget=None) == analysis


def test_apply_budget_to_analysis_enriches_additions(monkeypatch):
    import analyzer.budget as budget_module

    monkeypatch.setattr(
        budget_module.prices_module, "fetch_prices", lambda conn, names: {name: 3.0 for name in names}
    )
    analysis = {
        "anadidos_sugeridos": [make_addition("X", categoria_problema="Ramp")],
        "problemas": [{"categoria": "Ramp", "severidad": "alta", "explicacion": "..."}],
    }

    result = budget_module.apply_budget_to_analysis(conn=None, analysis=analysis, budget=10.0)

    assert result["anadidos_sugeridos"][0]["precio_eur"] == 3.0
    assert result["anadidos_sugeridos"][0]["incluido"] is True
    assert result["presupuesto"] == {
        "presupuesto": 10.0,
        "coste_estimado": 3.0,
        "supera_presupuesto": False,
        "diferencia": -7.0,
    }
