from compare_eval import compare


def make_record(
    deck="jasnah.txt",
    timestamp="2026-01-01T00:00:00+00:00",
    estrategia="control",
    arquetipo="enchantments",
    problemas=None,
):
    return {
        "deck": deck,
        "timestamp": timestamp,
        "validated_analysis": {
            "estrategia_detectada": estrategia,
            "arquetipo": arquetipo,
            "puntos_fuertes": [],
            "problemas": problemas or [],
        },
    }


def test_compare_reports_no_differences_when_identical():
    old = make_record()
    new = make_record(timestamp="2026-02-01T00:00:00+00:00")

    text = compare(old, new)

    assert "Sin diferencias relevantes" in text


def test_compare_detects_strategy_and_archetype_changes():
    old = make_record(estrategia="aggro", arquetipo="voltron")
    new = make_record(estrategia="control", arquetipo="enchantments")

    text = compare(old, new)

    assert "Estrategia: 'aggro' -> 'control'" in text
    assert "Arquetipo: 'voltron' -> 'enchantments'" in text


def test_compare_detects_added_and_removed_candidates():
    old = make_record(
        problemas=[
            {
                "categoria": "Ramp",
                "severidad": "media",
                "explicacion": "x",
                "candidatas_sugeridas": [{"carta": "Carta Vieja", "rol": "ramp", "motivo": "x"}],
            }
        ]
    )
    new = make_record(
        problemas=[
            {
                "categoria": "Ramp",
                "severidad": "media",
                "explicacion": "x",
                "candidatas_sugeridas": [{"carta": "Carta Nueva", "rol": "ramp", "motivo": "y"}],
            }
        ]
    )

    text = compare(old, new)

    assert "Candidatas nuevas: ['Carta Nueva']" in text
    assert "Candidatas que ya no se sugieren: ['Carta Vieja']" in text


def test_compare_detects_problem_category_changes():
    old = make_record(problemas=[{"categoria": "removal", "severidad": "alta", "explicacion": "x"}])
    new = make_record(problemas=[{"categoria": "ramp", "severidad": "media", "explicacion": "y"}])

    text = compare(old, new)

    assert "Categorías de problemas: ['removal'] -> ['ramp']" in text
