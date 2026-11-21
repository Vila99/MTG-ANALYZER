from analyzer.rubric import RoleRange, evaluate_role_counts


def test_role_range_below_minimum():
    assert RoleRange(10, 12).status(5) == "bajo"


def test_role_range_within_range():
    assert RoleRange(10, 12).status(11) == "ok"


def test_role_range_above_maximum():
    assert RoleRange(10, 12).status(15) == "alto"


def test_role_range_without_maximum_never_flags_alto():
    assert RoleRange(10, None).status(999) == "ok"


def test_evaluate_role_counts_missing_role_counts_as_zero():
    statuses = evaluate_role_counts({})
    assert statuses["land"] == "bajo"
    assert statuses["ramp"] == "bajo"


def test_evaluate_role_counts_balanced_deck():
    statuses = evaluate_role_counts(
        {"land": 36, "ramp": 11, "draw": 12, "removal": 9, "wipe": 3}
    )
    assert all(status == "ok" for status in statuses.values())
