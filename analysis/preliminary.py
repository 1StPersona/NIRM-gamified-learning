"""Анализ предварительных результатов (лекция 10): статистика и рисунки.

Входные данные: bench/results/simulation.csv (калибровка K), bench/results/policies.csv и
policies_students.csv (сравнение политик), bench/results/load.csv (нагрузочный тест).
Выход: docs/img/fig_zone_by_tercile.png, docs/img/fig_rmse_by_k.png, bench/results/preliminary_stats.json.

Запуск: python -m analysis.preliminary
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

RES = Path("bench/results")
IMG = Path("docs/img")
COL = {"linear": "#2a78d6", "adaptive": "#eb6834", "mixed": "#1baf7a", "random": "#6250d6"}
NAME = {"linear": "Линейный порядок (СГ)", "adaptive": "Адаптивный выбор (АГ)",
        "mixed": "АГ + 10 % случайных задач"}
INK, MUTED, GRID = "#0b0b0b", "#52514e", "#e4e3df"


def ci95(x) -> tuple[float, float, float]:
    x = np.asarray(x, dtype=float)
    m, se = x.mean(), x.std(ddof=1) / np.sqrt(len(x))
    h = se * stats.t.ppf(0.975, len(x) - 1)
    return float(m), float(m - h), float(m + h)


def cohen_d(a, b) -> float:
    a, b = np.asarray(a), np.asarray(b)
    sp = np.sqrt(((len(a) - 1) * a.var(ddof=1) + (len(b) - 1) * b.var(ddof=1)) / (len(a) + len(b) - 2))
    return float((a.mean() - b.mean()) / sp)


def style(ax):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(MUTED)
    ax.tick_params(colors=MUTED, labelcolor=INK)
    ax.yaxis.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)


def main() -> None:
    IMG.mkdir(parents=True, exist_ok=True)
    out: dict = {}
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10})

    # 1. Политики: доля попыток в зоне посильной сложности, по терцилям способностей
    st = pd.read_csv(RES / "policies_students.csv")
    pol = pd.read_csv(RES / "policies.csv")
    out["policies"] = {}
    for p in ("linear", "adaptive", "mixed"):
        s = st[st.policy == p]
        r = pol[pol.policy == p]
        out["policies"][p] = {
            "zone_share": ci95(r.zone_share), "success_rate": ci95(r.success_rate),
            "mean_gap": ci95(r.mean_gap), "logloss": ci95(r.logloss_elo),
            "zone_by_tercile": {int(t): ci95(g.zone_share) for t, g in s.groupby("tercile")},
            "success_by_tercile": {int(t): ci95(g.success_rate) for t, g in s.groupby("tercile")},
            "n_students": int(len(s)),
            "zone_by_tercile_quarter": {int(t): [float(g[f"zone_q{i}"].mean()) for i in range(1, 5)]
                                        for t, g in s.groupby("tercile")},
            "easy_by_tercile_quarter": {int(t): [float(g[f"easy_q{i}"].mean()) for i in range(1, 5)]
                                        for t, g in s.groupby("tercile")},
        }
    a, l = st[st.policy == "adaptive"].zone_share, st[st.policy == "linear"].zone_share
    t = stats.ttest_ind(a, l, equal_var=False)
    out["test_zone_adaptive_vs_linear"] = {"t": float(t.statistic), "p": float(t.pvalue),
                                          "df": float(t.df), "d": cohen_d(a, l),
                                          "diff": float(a.mean() - l.mean())}
    kw = stats.kruskal(*[st[st.policy == p].zone_share for p in ("linear", "adaptive", "mixed")])
    out["kruskal_zone"] = {"H": float(kw.statistic), "p": float(kw.pvalue)}
    # однородность по терцилям: разброс доли в зоне между терцилями
    out["tercile_spread"] = {p: float(np.ptp([v[0] for v in out["policies"][p]["zone_by_tercile"].values()]))
                             for p in ("linear", "adaptive")}

    fig, ax = plt.subplots(figsize=(6.4, 3.6), dpi=200)
    w = 0.26
    labels = ["Слабые\n(нижняя треть θ)", "Средние", "Сильные\n(верхняя треть θ)"]
    for i, p in enumerate(("linear", "adaptive", "mixed")):
        vals = out["policies"][p]["zone_by_tercile"]
        m = [vals[k][0] for k in range(3)]
        err = [[vals[k][0] - vals[k][1] for k in range(3)], [vals[k][2] - vals[k][0] for k in range(3)]]
        x = np.arange(3) + (i - 1) * (w + 0.02)
        ax.bar(x, m, w, color=COL[p], label=NAME[p], edgecolor="white", linewidth=1)
        ax.errorbar(x, m, yerr=err, fmt="none", ecolor=INK, elinewidth=1, capsize=3)
    ax.set_xticks(np.arange(3), labels)
    ax.set_ylim(0, 1)
    ax.set_ylabel("Доля попыток с 0,5 ≤ P(успех) ≤ 0,85", color=INK)
    style(ax)
    ax.legend(frameon=False, fontsize=8.5, loc="upper center", ncol=3, bbox_to_anchor=(0.5, 1.13))
    fig.tight_layout()
    fig.savefig(IMG / "fig_zone_by_tercile.png")
    plt.close(fig)

    # 2. Калибровка K: RMSE оценки θ
    sim = pd.read_csv(RES / "simulation.csv")
    out["k_calibration"] = {}
    for pname in ("adaptive", "random"):
        out["k_calibration"][pname] = {
            str(k): {"rmse": ci95(g.rmse_theta), "corr": ci95(g.corr_theta),
                     "success": ci95(g.success_rate_2nd_half), "logloss": ci95(g.logloss_elo),
                     "auc_elo": ci95(g.auc_elo), "auc_static": ci95(g.auc_static)}
            for k, g in sim[sim.policy == pname].groupby("K")}
    ad = sim[sim.policy == "adaptive"]
    an = stats.f_oneway(*[g.rmse_theta for _, g in ad.groupby("K")])
    ss_b = sum(len(g) * (g.rmse_theta.mean() - ad.rmse_theta.mean()) ** 2 for _, g in ad.groupby("K"))
    ss_t = ((ad.rmse_theta - ad.rmse_theta.mean()) ** 2).sum()
    out["anova_rmse_adaptive"] = {"F": float(an.statistic), "p": float(an.pvalue), "eta2": float(ss_b / ss_t)}
    r1 = ad[ad.K == 0.1].sort_values("rep").rmse_theta.values
    r2 = ad[ad.K == 0.2].sort_values("rep").rmse_theta.values
    pt = stats.ttest_rel(r1, r2)
    out["paired_rmse_k01_vs_k02"] = {"t": float(pt.statistic), "p": float(pt.pvalue),
                                     "diff": ci95(r1 - r2)}
    succ = ad.success_rate_2nd_half
    one = stats.ttest_1samp(succ, 0.7)
    out["success_vs_target"] = {"mean": ci95(succ), "t": float(one.statistic), "p": float(one.pvalue)}

    fig, ax = plt.subplots(figsize=(6.4, 3.4), dpi=200)
    ks = sorted(sim.K.unique())
    for pname, mk, lab, col in (("adaptive", "o", "Адаптивный выбор задач", COL["adaptive"]),
                                ("random", "s", "Случайный выбор задач", COL["random"])):
        d = out["k_calibration"][pname]
        m = [d[str(k)]["rmse"][0] for k in ks]
        err = [[d[str(k)]["rmse"][0] - d[str(k)]["rmse"][1] for k in ks],
               [d[str(k)]["rmse"][2] - d[str(k)]["rmse"][0] for k in ks]]
        ax.errorbar(ks, m, yerr=err, marker=mk, markersize=6, linewidth=2, capsize=3, color=col, label=lab)
    ax.set_xscale("log", base=2)
    ax.set_xticks(ks, [str(k).replace(".", ",") for k in ks])
    ax.minorticks_off()
    ax.set_xlabel("Шаг обновления рейтинга студента K", color=INK)
    ax.set_ylabel("RMSE оценки способности θ, логиты", color=INK)
    ax.annotate("выбрано K = 0,2", xy=(0.2, out["k_calibration"]["adaptive"]["0.2"]["rmse"][0]),
                xytext=(0.13, 1.2), arrowprops={"arrowstyle": "->", "color": MUTED}, color=INK, fontsize=9)
    style(ax)
    ax.legend(frameon=False, fontsize=9)
    fig.tight_layout()
    fig.savefig(IMG / "fig_rmse_by_k.png")
    plt.close(fig)

    # 3. RQ3: AUC на случайно выданных задачах (политика mixed)
    mx = pol[pol.policy == "mixed"].sort_values("rep")
    diff = mx.auc_elo_explore.values - mx.auc_static_explore.values
    pr = stats.ttest_rel(mx.auc_elo_explore, mx.auc_static_explore)
    out["rq3_mixed"] = {"auc_elo": ci95(mx.auc_elo_explore), "auc_static": ci95(mx.auc_static_explore),
                        "diff": ci95(diff), "t": float(pr.statistic), "p": float(pr.pvalue),
                        "n_explore_mean": float(mx.n_explore.mean())}
    rnd = sim[(sim.policy == "random") & (sim.K == 0.2)].sort_values("rep")
    pr2 = stats.ttest_rel(rnd.auc_elo, rnd.auc_static)
    out["rq3_random_k02"] = {"diff": ci95(rnd.auc_elo.values - rnd.auc_static.values),
                             "t": float(pr2.statistic), "p": float(pr2.pvalue)}

    # 4. Нагрузка: p95 при 64 клиентах против цели 100 мс
    ld = pd.read_csv(RES / "load.csv")
    out["load_p95_64"] = {s: ci95(g.p95_ms) for s, g in ld[ld.concurrency == 64].groupby("store")}

    # 5. Проверка устойчивости (ответ рецензенту, лекция 13): неверно заданная модель и тёплый старт
    out["variants"] = {}
    for v in ("misspec", "warm"):
        pv, sv = RES / f"policies_{v}.csv", RES / f"policies_students_{v}.csv"
        if not pv.exists():
            continue
        pol_v, st_v = pd.read_csv(pv), pd.read_csv(sv)
        res = {}
        for p in ("linear", "adaptive", "mixed"):
            r, s_ = pol_v[pol_v.policy == p], st_v[st_v.policy == p]
            res[p] = {"zone_share": ci95(r.zone_share), "success_rate": ci95(r.success_rate),
                      "zone_by_tercile": {int(t): ci95(g.zone_share) for t, g in s_.groupby("tercile")},
                      "strong_q1_easy": float(s_[s_.tercile == 2].easy_q1.mean()),
                      "strong_q1_zone": float(s_[s_.tercile == 2].zone_q1.mean())}
        a_, l_ = st_v[st_v.policy == "adaptive"].zone_share, st_v[st_v.policy == "linear"].zone_share
        res["d_adaptive_vs_linear"] = cohen_d(a_, l_)
        mx_ = pol_v[pol_v.policy == "mixed"]
        res["rq3_diff"] = ci95(mx_.auc_elo_explore.values - mx_.auc_static_explore.values)
        res["rq3_auc"] = [ci95(mx_.auc_elo_explore), ci95(mx_.auc_static_explore)]
        out["variants"][v] = res

    (RES / "preliminary_stats.json").write_text(json.dumps(out, ensure_ascii=False, indent=1))
    print(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
