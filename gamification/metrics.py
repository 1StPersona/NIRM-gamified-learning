"""Метрики активности и индекс вовлечённости (глава 2.1, формулы 2.1–2.5)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

# Веса индекса по умолчанию. Перед экспериментом фиксируются в experiment config
# (см. лекцию 7: веса не меняются после начала сбора данных).
DEFAULT_WEIGHTS: Mapping[str, float] = {"activity": 0.4, "completion": 0.4, "stability": 0.2}


@dataclass(frozen=True)
class UserPeriodStats:
    sessions: int          # Ns(u) — число учебных сессий за период
    period_days: float     # T — длина периода наблюдения, дни
    attempted: int         # число задач, к которым приступал пользователь
    solved: int            # число решённых задач
    active_days: int       # дни с хотя бы одной сессией


def activity_rate(s: UserPeriodStats) -> float:
    """AR(u) = Ns(u) / T, сессий в день (2.1)."""
    if s.period_days <= 0:
        raise ValueError("period_days must be positive")
    return s.sessions / s.period_days


def completion_rate(s: UserPeriodStats) -> float:
    """CR(u) = решённые / начатые (2.2); 0, если пользователь ничего не начинал."""
    if s.solved > s.attempted:
        raise ValueError("solved cannot exceed attempted")
    return s.solved / s.attempted if s.attempted else 0.0


def stability(s: UserPeriodStats) -> float:
    """Устойчивость занятий: доля дней периода с активностью (2.3)."""
    if s.period_days <= 0:
        raise ValueError("period_days must be positive")
    return min(1.0, s.active_days / s.period_days)


def min_max(value: float, lo: float, hi: float) -> float:
    """Линейная нормализация в [0, 1] (2.4) с отсечением выбросов."""
    if hi <= lo:
        return 0.0
    return max(0.0, min(1.0, (value - lo) / (hi - lo)))


def engagement_index(
    s: UserPeriodStats,
    ar_bounds: tuple[float, float] = (0.0, 2.0),
    weights: Mapping[str, float] = DEFAULT_WEIGHTS,
) -> float:
    """EI(u) = Σ w_k · x̃_k(u), Σ w_k = 1 (2.5)."""
    if abs(sum(weights.values()) - 1.0) > 1e-9:
        raise ValueError("weights must sum to 1")
    x = {
        "activity": min_max(activity_rate(s), *ar_bounds),
        "completion": completion_rate(s),
        "stability": stability(s),
    }
    return sum(weights[k] * x[k] for k in weights)


def engagement_indices(stats: Sequence[UserPeriodStats], **kw) -> list[float]:
    return [engagement_index(s, **kw) for s in stats]
