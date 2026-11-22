from analyzer.scoring import compute_deck_score


def all_ok_rubric() -> dict:
    return {"land": "ok", "ramp": "ok", "draw": "ok", "removal": "ok", "wipe": "ok"}


def test_perfect_rubric_without_problems_scores_ten():
    assert compute_deck_score(all_ok_rubric()) == 10.0


def test_each_rubric_issue_subtracts_points():
    rubric = {**all_ok_rubric(), "ramp": "bajo", "wipe": "alto"}
    assert compute_deck_score(rubric) < compute_deck_score(all_ok_rubric())


def test_alta_severidad_subtracts_more_than_media_and_baja():
    rubric = all_ok_rubric()
    alta = compute_deck_score(rubric, [{"severidad": "alta"}])
    media = compute_deck_score(rubric, [{"severidad": "media"}])
    baja = compute_deck_score(rubric, [{"severidad": "baja"}])
    assert alta < media <= baja <= 10.0


def test_score_never_goes_below_zero():
    rubric = {"land": "bajo", "ramp": "bajo", "draw": "bajo", "removal": "bajo", "wipe": "bajo"}
    problemas = [{"severidad": "alta"}] * 10
    assert compute_deck_score(rubric, problemas) == 0.0


def test_score_rounds_to_nearest_half_point():
    rubric = {**all_ok_rubric(), "ramp": "bajo"}  # 10 - 0.6 = 9.4 -> redondea a 9.5
    assert compute_deck_score(rubric) == 9.5


def test_unknown_severity_is_ignored():
    rubric = all_ok_rubric()
    assert compute_deck_score(rubric, [{"severidad": "desconocida"}]) == 10.0


def test_works_without_problemas_argument():
    assert compute_deck_score(all_ok_rubric()) == compute_deck_score(all_ok_rubric(), None)
