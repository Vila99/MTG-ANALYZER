from analyzer.cards import Card
from analyzer.report import build_summary, cards_by_role, render, render_analysis


def make_card(name: str, type_line: str = "Creature", color_identity=None) -> Card:
    return Card(
        name=name,
        mana_cost="",
        cmc=2.0,
        type_line=type_line,
        oracle_text="",
        colors=[],
        color_identity=color_identity or [],
        produced_mana=[],
        legalities={"commander": "legal"},
    )


def test_render_shows_missing_cards():
    text = render([], [], ["Phantom Card"])
    assert "Phantom Card" in text
    assert "no se detectó comandante" in text


def test_render_shows_role_counts_and_rubric_status():
    commander = make_card("Atraxa", color_identity=["W", "U", "B", "G"])
    deck_cards = [make_card("Sol Ring", type_line="Artifact")]
    text = render(
        [commander],
        deck_cards,
        [],
        role_counts={"ramp": 5},
        rubric_status={"land": "bajo", "ramp": "ok"},
    )
    assert "Ramp: 5" in text
    assert "dentro de rango" in text
    assert "bajo" in text


def test_render_analysis_includes_all_sections():
    analysis = {
        "estrategia_detectada": "superfriends",
        "arquetipo": "planeswalkers",
        "puntos_fuertes": ["buena ventaja de cartas"],
        "problemas": [
            {"categoria": "removal", "severidad": "alta", "explicacion": "muy poco removal"}
        ],
        "cortes_sugeridos": [{"carta": "Carta Mala", "motivo": "no aporta nada"}],
        "anadidos_sugeridos": [
            {
                "carta": "Carta Buena",
                "rol": "removal",
                "reemplaza_a": "Carta Mala",
                "motivo": "mejora la interacción",
            }
        ],
    }

    text = render_analysis(analysis)

    assert "superfriends" in text
    assert "planeswalkers" in text
    assert "buena ventaja de cartas" in text
    assert "[alta] removal: muy poco removal" in text
    assert "Carta Mala: no aporta nada" in text
    assert "Carta Buena [removal] (reemplaza a Carta Mala): mejora la interacción" in text


def test_render_analysis_handles_empty_sections():
    analysis = {
        "estrategia_detectada": "aggro",
        "arquetipo": "voltron",
        "puntos_fuertes": [],
        "problemas": [],
        "cortes_sugeridos": [],
        "anadidos_sugeridos": [],
    }
    text = render_analysis(analysis)
    assert "aggro" in text
    assert "voltron" in text


def test_cards_by_role_inverts_name_to_roles_mapping():
    card_roles = {
        "Sol Ring": ["ramp"],
        "Arcane Signet": ["ramp"],
        "Rhystic Study": ["draw"],
    }
    result = cards_by_role(card_roles)
    assert result["ramp"] == ["Sol Ring", "Arcane Signet"]
    assert result["draw"] == ["Rhystic Study"]


def test_cards_by_role_does_not_duplicate_a_card_counted_twice_in_the_same_role():
    card_roles = {"Sol Ring": ["ramp", "ramp"]}
    result = cards_by_role(card_roles)
    assert result["ramp"] == ["Sol Ring"]


def test_build_summary_includes_cartas_por_rol_when_card_roles_given():
    summary = build_summary([], [], [], {}, {}, card_roles={"Sol Ring": ["ramp"]})
    assert summary["cartas_por_rol"] == {"ramp": ["Sol Ring"]}


def test_build_summary_omits_cartas_por_rol_when_not_given():
    summary = build_summary([], [], [], {}, {})
    assert "cartas_por_rol" not in summary


def test_build_summary_includes_nota_deck_from_rubric_alone():
    rubric_status = {"land": "ok", "ramp": "ok", "draw": "ok", "removal": "ok", "wipe": "ok"}
    summary = build_summary([], [], [], {}, rubric_status)
    assert summary["nota_deck"] == 10.0


def test_build_summary_includes_identidad_color_in_wubrg_order():
    commanders = [
        make_card("Commander A", color_identity=["B", "G"]),
        make_card("Commander B", color_identity=["W"]),
    ]
    summary = build_summary(commanders, [], [], {}, {})
    assert summary["identidad_color"] == ["W", "B", "G"]


def test_build_summary_identidad_color_empty_for_colorless_commander():
    summary = build_summary([make_card("Commander", color_identity=[])], [], [], {}, {})
    assert summary["identidad_color"] == []


def test_build_summary_includes_nota_deck_lowered_by_problemas():
    rubric_status = {"land": "ok", "ramp": "ok", "draw": "ok", "removal": "ok", "wipe": "ok"}
    summary = build_summary(
        [], [], [], {}, rubric_status, problemas=[{"categoria": "x", "severidad": "alta", "explicacion": "y"}]
    )
    assert summary["nota_deck"] < 10.0
