"""Сравнение политик выбора задач на синтетических студентах (лекция 10, предварительные результаты).

Модель студентов и задач та же, что в simulation/simulate.py: θ* ~ N(0, 1), 50 задач с d* на [−2.5, 2.4],
исход попытки разыгрывается по логистической модели, система видит только исходы.

Политики:
  linear   — аналог СГ: задачи упорядочены по метке сложности, после успеха студент переходит к следующей,
             после неудачи повторяет ту же;
  adaptive — АГ: задача с P(θ̂, d̂) ближе всего к p* = 0,7 (формула 2.12);
  mixed    — АГ, но с вероятностью ε = 0,1 задача выбирается случайно (план RQ3 после лекции 8).

Для каждой попытки сохраняется истинная вероятность успеха p*, по ней считается доля попыток
в «зоне посильной сложности» 0,5 ≤ p ≤ 0,85.

Запуск: python -m simulation.policies --seed 42 --reps 5
"""
from __future__ import annotations

import argparse
import csv

import numpy as np

from gamification import adaptive
from simulation.simulate import auc

N_STUDENTS = 300
N_ATTEMPTS = 60
EPS = 0.1
ZONE = (0.5, 0.85)
K = 0.2


def run(policy: str, rng: np.random.Generator, variant: str = "base") -> tuple[dict, list[dict]]:
    """variant: base — как в simulate.py; misspec — истинная модель отличается от модели Эло
    (угадывание 0,1, ошибка по невнимательности 0,1, рост способности на 0,02 после каждого успеха);
    warm — начальная оценка θ берётся из пре-теста: истинная θ плюс шум N(0; 0,5)."""
    guess, slip, learn = (0.1, 0.1, 0.02) if variant == "misspec" else (0.0, 0.0, 0.0)
    true_theta = rng.normal(0.0, 1.0, N_STUDENTS)
    theta0 = true_theta.copy()
    task_ids = [f"q{i:02d}" for i in range(50)]
    true_d = dict(zip(task_ids, np.linspace(-2.5, 2.4, 50)))
    static_label = {q: round(float(true_d[q])) for q in task_ids}
    order = sorted(task_ids, key=lambda q: (static_label[q], q))
    est_d = {q: 0.0 for q in task_ids}
    est_theta = np.zeros(N_STUDENTS)
    if variant == "warm":
        est_theta = true_theta + rng.normal(0.0, 0.5, N_STUDENTS)
    pos = np.zeros(N_STUDENTS, dtype=int)          # позиция студента в линейном порядке
    solved_n = np.zeros(N_STUDENTS)
    in_zone = np.zeros(N_STUDENTS)
    gap = np.zeros(N_STUDENTS)
    zone_q = np.zeros((N_STUDENTS, 4))           # доля в зоне по четвертям попыток
    easy_q = np.zeros((N_STUDENTS, 4))           # доля слишком лёгких задач (p > 0,85)
    explo_elo, explo_static, explo_y = [], [], []
    all_elo, all_y = [], []

    for t in range(N_ATTEMPTS):
        quarter = t * 4 // N_ATTEMPTS
        for s in rng.permutation(N_STUDENTS):
            explore = False
            if policy == "linear":
                q = order[min(pos[s], len(order) - 1)]
            elif policy == "mixed" and rng.random() < EPS:
                q, explore = task_ids[rng.integers(50)], True
            else:
                q = adaptive.select_task(est_theta[s], est_d)
            p_true = guess + (1 - guess - slip) * adaptive.p_success(true_theta[s], true_d[q])
            ok = rng.random() < p_true
            pe = adaptive.p_success(est_theta[s], est_d[q])
            all_elo.append(pe)
            all_y.append(int(ok))
            if explore:
                explo_elo.append(pe)
                explo_static.append(adaptive.p_success(0.0, static_label[q]))
                explo_y.append(int(ok))
            solved_n[s] += ok
            in_zone[s] += ZONE[0] <= p_true <= ZONE[1]
            gap[s] += abs(p_true - adaptive.TARGET_P)
            zone_q[s, quarter] += ZONE[0] <= p_true <= ZONE[1]
            easy_q[s, quarter] += p_true > ZONE[1]
            if ok:
                true_theta[s] += learn
            if policy == "linear" and ok:
                pos[s] += 1
            est_theta[s], est_d[q] = adaptive.elo_update(est_theta[s], est_d[q], ok, k_student=K, k_task=K / 2)

    terc = np.digitize(theta0, np.quantile(theta0, [1 / 3, 2 / 3]))  # 0 слабые, 1 средние, 2 сильные
    per_student = [
        {"policy": policy, "theta": float(theta0[s]), "tercile": int(terc[s]),
         "success_rate": solved_n[s] / N_ATTEMPTS, "zone_share": in_zone[s] / N_ATTEMPTS,
         "mean_gap": gap[s] / N_ATTEMPTS,
         **{f"zone_q{i + 1}": zone_q[s, i] / (N_ATTEMPTS / 4) for i in range(4)},
         **{f"easy_q{i + 1}": easy_q[s, i] / (N_ATTEMPTS / 4) for i in range(4)}}
        for s in range(N_STUDENTS)
    ]
    y, p = np.array(all_y), np.clip(np.array(all_elo), 1e-6, 1 - 1e-6)
    summary = {
        "policy": policy,
        "success_rate": float(y.mean()),
        "zone_share": float(in_zone.sum() / (N_STUDENTS * N_ATTEMPTS)),
        "mean_gap": float(gap.sum() / (N_STUDENTS * N_ATTEMPTS)),
        "logloss_elo": float(-np.mean(y * np.log(p) + (1 - y) * np.log(1 - p))),
        "auc_elo_all": auc(p, y),
        "n_explore": len(explo_y),
        "auc_elo_explore": auc(np.array(explo_elo), np.array(explo_y)) if explo_y else float("nan"),
        "auc_static_explore": auc(np.array(explo_static), np.array(explo_y)) if explo_y else float("nan"),
    }
    return summary, per_student


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--reps", type=int, default=5)
    ap.add_argument("--variant", choices=("base", "misspec", "warm"), default="base")
    a = ap.parse_args()
    suffix = "" if a.variant == "base" else f"_{a.variant}"
    a.out = f"bench/results/policies{suffix}.csv"
    a.students_out = f"bench/results/policies_students{suffix}.csv"
    rows, students = [], []
    for policy in ("linear", "adaptive", "mixed"):
        for rep in range(a.reps):
            summ, per = run(policy, np.random.default_rng(a.seed + rep), a.variant)
            summ["rep"] = rep
            rows.append(summ)
            for r in per:
                r["rep"] = rep
            students.extend(per)
    for path, data in ((a.out, rows), (a.students_out, students)):
        with open(path, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(data[0]))
            w.writeheader()
            w.writerows(data)
    for policy in ("linear", "adaptive", "mixed"):
        sub = [r for r in rows if r["policy"] == policy]
        print(policy, {m: round(float(np.mean([r[m] for r in sub])), 3)
                       for m in sub[0] if m not in ("policy", "rep")})


if __name__ == "__main__":
    main()
