import pytest

from gamification import progression as pr


def test_first_try_without_streak_gives_base_xp():
    assert pr.xp_for_solution(1.0, attempts=1, streak_days=0) == pr.BASE_XP


def test_extra_attempts_reduce_xp():
    assert pr.xp_for_solution(1.0, 3, 0) < pr.xp_for_solution(1.0, 1, 0)


def test_streak_bonus_is_capped():
    assert pr.xp_for_solution(1.0, 1, 50) == pr.xp_for_solution(1.0, 1, pr.STREAK_CAP)


@pytest.mark.parametrize("level", range(1, 15))
def test_level_formula_is_inverse_of_threshold(level):
    threshold = pr.xp_to_reach(level)
    assert pr.level_for_xp(threshold) == level
    if level > 1:
        assert pr.level_for_xp(threshold - 1) == level - 1


def test_badges_are_awarded_once():
    p = pr.Profile()
    _, new = pr.apply_solution(p, 1.0, attempts=1)
    assert new == {"first_blood"}
    _, new = pr.apply_solution(p, 1.0, attempts=1)
    assert new == set()


def test_invalid_attempts_rejected():
    with pytest.raises(ValueError):
        pr.xp_for_solution(1.0, 0, 0)
