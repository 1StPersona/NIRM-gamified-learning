import math

import pytest

from gamification import adaptive


def test_equal_rating_gives_even_chance():
    assert adaptive.p_success(0.3, 0.3) == pytest.approx(0.5)


def test_success_raises_student_and_lowers_task():
    theta, d = adaptive.elo_update(0.0, 0.0, solved=True)
    assert theta > 0.0 and d < 0.0


def test_failure_lowers_student_and_raises_task():
    theta, d = adaptive.elo_update(0.0, 0.0, solved=False)
    assert theta < 0.0 and d > 0.0


def test_update_is_zero_sum_when_k_equal():
    theta, d = adaptive.elo_update(1.0, -0.5, solved=False, k_student=0.3, k_task=0.3)
    assert (theta - 1.0) == pytest.approx(-(d - -0.5))


def test_selected_task_is_closest_to_target_probability():
    tasks = {"easy": -3.0, "target": -math.log(0.7 / 0.3), "hard": 3.0}
    assert adaptive.select_task(0.0, tasks) == "target"


def test_select_task_requires_tasks():
    with pytest.raises(ValueError):
        adaptive.select_task(0.0, {})
