"""Модель геймификации: опыт, уровни, значки (глава 2.2, формулы 2.6–2.9)."""
from __future__ import annotations

import math
from dataclasses import dataclass, field

BASE_XP = 100        # опыт за задачу сложности 1.0
ATTEMPT_PENALTY = 0.85   # ρ: множитель за каждую лишнюю попытку
STREAK_BONUS = 0.05      # β: +5 % за каждый день серии
STREAK_CAP = 10          # бонус серии не растёт после 10 дней
LEVEL_BASE = 200         # X0: опыт до 2-го уровня
LEVEL_RATIO = 1.5        # q: знаменатель геометрической прогрессии уровней


def xp_for_solution(difficulty: float, attempts: int, streak_days: int) -> int:
    """XP = BASE · d · ρ^(attempts−1) · (1 + β · min(streak, cap)) (2.6)."""
    if attempts < 1:
        raise ValueError("attempts must be >= 1")
    if difficulty <= 0:
        raise ValueError("difficulty must be positive")
    bonus = 1 + STREAK_BONUS * min(max(streak_days, 0), STREAK_CAP)
    return round(BASE_XP * difficulty * ATTEMPT_PENALTY ** (attempts - 1) * bonus)


def xp_to_reach(level: int) -> int:
    """Суммарный опыт для уровня L: X0 · (q^(L−1) − 1) / (q − 1) (2.7)."""
    if level < 1:
        raise ValueError("level must be >= 1")
    return round(LEVEL_BASE * (LEVEL_RATIO ** (level - 1) - 1) / (LEVEL_RATIO - 1))


def level_for_xp(xp: int) -> int:
    """Обратная формула уровня (2.8)."""
    if xp < 0:
        raise ValueError("xp must be >= 0")
    level = 1 + math.floor(math.log(1 + xp * (LEVEL_RATIO - 1) / LEVEL_BASE, LEVEL_RATIO))
    # защита от ошибок округления на границе уровня
    while xp_to_reach(level + 1) <= xp:
        level += 1
    while level > 1 and xp_to_reach(level) > xp:
        level -= 1
    return level


@dataclass
class Profile:
    xp: int = 0
    solved: int = 0
    streak_days: int = 0
    first_try_solved: int = 0
    badges: set[str] = field(default_factory=set)

    @property
    def level(self) -> int:
        return level_for_xp(self.xp)


# Значки как предикаты над профилем (2.9)
BADGES = {
    "first_blood": lambda p: p.solved >= 1,
    "ten_quests": lambda p: p.solved >= 10,
    "streak_7": lambda p: p.streak_days >= 7,
    "sniper": lambda p: p.first_try_solved >= 5,
}


def apply_solution(p: Profile, difficulty: float, attempts: int) -> tuple[int, set[str]]:
    """Начисляет опыт и возвращает (полученный XP, новые значки)."""
    gained = xp_for_solution(difficulty, attempts, p.streak_days)
    p.xp += gained
    p.solved += 1
    if attempts == 1:
        p.first_try_solved += 1
    new = {name for name, rule in BADGES.items() if name not in p.badges and rule(p)}
    p.badges |= new
    return gained, new
