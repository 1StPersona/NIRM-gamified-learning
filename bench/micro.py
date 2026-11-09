"""Микробенчмарки функций модели (лекция 8): время одного вызова, мкс."""
from __future__ import annotations

import json
import platform
import statistics
import timeit

from gamification import adaptive, metrics, progression
from services.gamification_api.app import TASKS

STATS = metrics.UserPeriodStats(sessions=20, period_days=28, attempted=30, solved=21, active_days=14)

CASES = {
    "p_success": lambda: adaptive.p_success(0.3, -0.2),
    "elo_update": lambda: adaptive.elo_update(0.3, -0.2, True),
    "select_task_50": lambda: adaptive.select_task(0.3, TASKS),
    "xp_for_solution": lambda: progression.xp_for_solution(1.2, 2, 3),
    "level_for_xp": lambda: progression.level_for_xp(12_345),
    "engagement_index": lambda: metrics.engagement_index(STATS),
}


def main() -> None:
    out = {"python": platform.python_version(), "machine": platform.machine(), "results": {}}
    for name, fn in CASES.items():
        n = 20_000 if name != "select_task_50" else 2_000
        runs = timeit.repeat(fn, number=n, repeat=7)
        per_call = [r / n * 1e6 for r in runs]
        out["results"][name] = {"median_us": round(statistics.median(per_call), 3),
                                "min_us": round(min(per_call), 3), "max_us": round(max(per_call), 3)}
        print(f"{name:18s} median {statistics.median(per_call):8.3f} us  (min {min(per_call):.3f}, max {max(per_call):.3f})")
    with open("bench/results/micro.json", "w") as f:
        json.dump(out, f, indent=2)


if __name__ == "__main__":
    main()
