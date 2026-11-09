"""Адаптивный подбор сложности по рейтингу Эло (глава 2.3, формулы 2.10–2.12)."""
from __future__ import annotations

import math
from typing import Mapping

TARGET_P = 0.7   # p*: целевая вероятность успеха
K_STUDENT = 0.2  # шаг обновления рейтинга студента (выбран в simulation/, см. bench/results)
K_TASK = 0.1     # шаг обновления сложности задачи


def p_success(theta: float, difficulty: float) -> float:
    """P(успех) = 1 / (1 + e^−(θ − d)) (2.10)."""
    return 1.0 / (1.0 + math.exp(-(theta - difficulty)))


def elo_update(
    theta: float, difficulty: float, solved: bool,
    k_student: float = K_STUDENT, k_task: float = K_TASK,
) -> tuple[float, float]:
    """θ ← θ + K(s − P), d ← d − K_d(s − P) (2.11)."""
    err = (1.0 if solved else 0.0) - p_success(theta, difficulty)
    return theta + k_student * err, difficulty - k_task * err


def select_task(theta: float, tasks: Mapping[str, float], target: float = TARGET_P) -> str:
    """q* = argmin_q |P(θ, d_q) − p*| (2.12). Ничья — по id, чтобы выбор был детерминированным."""
    if not tasks:
        raise ValueError("no tasks to choose from")
    return min(sorted(tasks), key=lambda q: abs(p_success(theta, tasks[q]) - target))
