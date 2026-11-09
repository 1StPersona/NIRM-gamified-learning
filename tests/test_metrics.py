import pytest

from gamification import metrics as m

ACTIVE = m.UserPeriodStats(sessions=28, period_days=28, attempted=20, solved=15, active_days=21)
IDLE = m.UserPeriodStats(sessions=2, period_days=28, attempted=4, solved=1, active_days=2)


def test_rates():
    assert m.activity_rate(ACTIVE) == pytest.approx(1.0)
    assert m.completion_rate(ACTIVE) == pytest.approx(0.75)
    assert m.stability(ACTIVE) == pytest.approx(0.75)


def test_completion_rate_without_attempts_is_zero():
    s = m.UserPeriodStats(sessions=1, period_days=7, attempted=0, solved=0, active_days=1)
    assert m.completion_rate(s) == 0.0


def test_engagement_index_is_bounded_and_ordered():
    hi, lo = m.engagement_index(ACTIVE), m.engagement_index(IDLE)
    assert 0.0 <= lo < hi <= 1.0


def test_weights_must_sum_to_one():
    with pytest.raises(ValueError):
        m.engagement_index(ACTIVE, weights={"activity": 0.5, "completion": 0.5, "stability": 0.5})


def test_min_max_clips_outliers():
    assert m.min_max(5.0, 0.0, 2.0) == 1.0
    assert m.min_max(-1.0, 0.0, 2.0) == 0.0
