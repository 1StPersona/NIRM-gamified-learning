"""Калибровка шага K рейтинга Эло на синтетических студентах (этап 2 плана исследования).

Истинные способности студентов θ* ~ N(0, 1), истинные сложности задач d* равномерно
на [−2.5, 2.4]. Успех попытки разыгрывается по логистической модели от истинных
значений; система видит только исходы и оценивает θ, d своим правилом Эло.

Запуск: python -m simulation.simulate --seed 42 --out bench/results/simulation.csv
"""
from __future__ import annotations

import argparse
import csv

import numpy as np

from gamification import adaptive

N_STUDENTS = 300
N_ATTEMPTS = 60
K_GRID = [0.1, 0.2, 0.4, 0.8]


def auc(scores: np.ndarray, labels: np.ndarray) -> float:
    """AUC через ранги (Манн–Уитни), без внешних зависимостей."""
    order = scores.argsort()
    ranks = np.empty(len(scores))
    ranks[order] = np.arange(1, len(scores) + 1)
    pos = labels.sum()
    neg = len(labels) - pos
    return float((ranks[labels == 1].sum() - pos * (pos + 1) / 2) / (pos * neg))


def run(k: float, rng: np.random.Generator, policy: str = "adaptive") -> dict:
    true_theta = rng.normal(0.0, 1.0, N_STUDENTS)
    task_ids = [f"q{i:02d}" for i in range(50)]
    true_d = dict(zip(task_ids, np.linspace(-2.5, 2.4, 50)))
    est_d = {q: 0.0 for q in task_ids}            # система не знает сложностей заранее
    static_label = {q: round(float(true_d[q])) for q in task_ids}  # «метка преподавателя»: целая часть сложности
    est_theta = np.zeros(N_STUDENTS)
    pred_elo, pred_static, outcome, late_success = [], [], [], []

    for t in range(N_ATTEMPTS):
        for s in rng.permutation(N_STUDENTS):
            q = adaptive.select_task(est_theta[s], est_d) if policy == "adaptive" else task_ids[rng.integers(50)]
            p_true = adaptive.p_success(true_theta[s], true_d[q])
            solved = rng.random() < p_true
            pred_elo.append(adaptive.p_success(est_theta[s], est_d[q]))
            pred_static.append(adaptive.p_success(0.0, static_label[q]))
            outcome.append(int(solved))
            if t >= N_ATTEMPTS // 2:
                late_success.append(int(solved))
            est_theta[s], est_d[q] = adaptive.elo_update(est_theta[s], est_d[q], solved, k_student=k, k_task=k / 2)

    y = np.array(outcome)
    pe = np.clip(np.array(pred_elo), 1e-6, 1 - 1e-6)
    return {
        "policy": policy,
        "K": k,
        "rmse_theta": float(np.sqrt(np.mean((est_theta - true_theta) ** 2))),
        "corr_theta": float(np.corrcoef(est_theta, true_theta)[0, 1]),
        "success_rate_2nd_half": float(np.mean(late_success)),
        "auc_elo": auc(pe, y),
        "auc_static": auc(np.array(pred_static), y),
        "logloss_elo": float(-np.mean(y * np.log(pe) + (1 - y) * np.log(1 - pe))),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--reps", type=int, default=5)
    ap.add_argument("--out", default="bench/results/simulation.csv")
    a = ap.parse_args()
    rows = []
    for policy in ("adaptive", "random"):
        for k in K_GRID:
            for rep in range(a.reps):
                r = run(k, np.random.default_rng(a.seed + rep), policy)
                r["rep"] = rep
                rows.append(r)
    with open(a.out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    for policy in ("adaptive", "random"):
        for k in K_GRID:
            sub = [r for r in rows if r["K"] == k and r["policy"] == policy]
            mean = {m: np.mean([r[m] for r in sub]) for m in sub[0] if m not in ("policy", "K", "rep")}
            sd = np.std([r["success_rate_2nd_half"] for r in sub])
            print(f"{policy:8s} K={k}: " + ", ".join(f"{m}={v:.3f}" for m, v in mean.items()) + f", sd_success={sd:.3f}")


if __name__ == "__main__":
    main()
