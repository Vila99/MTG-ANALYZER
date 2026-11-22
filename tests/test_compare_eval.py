from compare_eval import compare


def make_record(
    deck="jasnah.txt",
    timestamp="2026-01-01T00:00:00+00:00",
    estrategia="control",
    arquetipo="enchantments",
    cortes=None,
    añadidos=None,
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
            "cortes_sugeridos": cortes or [],
            "añadidos_sugeridos": añadidos or [],
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


def test_compare_detects_added_and_removed_cuts_and_additions():
    old = make_record(
        cortes=[{"carta": "Carta Vieja", "motivo": "x"}],
        añadidos=[{"carta": "Add Vieja", "rol": "ramp", "reemplaza_a": None, "motivo": "x"}],
    )
    new = make_record(
        cortes=[{"carta": "Carta Nueva", "motivo": "y"}],
        añadidos=[{"carta": "Add Nueva", "rol": "draw", "reemplaza_a": None, "motivo": "y"}],
    )

    text = compare(old, new)

    assert "Cortes nuevos: ['Carta Nueva']" in text
    assert "Cortes que ya no se sugieren: ['Carta Vieja']" in text
    assert "Añadidos nuevos: ['Add Nueva']" in text
    assert "Añadidos que ya no se sugieren: ['Add Vieja']" in text


def test_compare_detects_problem_category_changes():
    old = make_record(problemas=[{"categoria": "removal", "severidad": "alta", "explicacion": "x"}])
    new = make_record(problemas=[{"categoria": "ramp", "severidad": "media", "explicacion": "y"}])

    text = compare(old, new)

    assert "Categorías de problemas: ['removal'] -> ['ramp']" in text
