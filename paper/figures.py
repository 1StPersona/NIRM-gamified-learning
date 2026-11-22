"""Vector figures (English labels) for the IEEE paper. Run from repo root: python -m paper.figures"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

S = json.loads(Path("bench/results/preliminary_stats.json").read_text())
OUT = Path("paper/figures")
COL = {"linear": "#2a78d6", "adaptive": "#eb6834", "mixed": "#1baf7a", "random": "#6250d6"}
NAME = {"linear": "Linear order (static)", "adaptive": "Adaptive (Elo)", "mixed": "Adaptive + 10% random"}
INK, MUTED, GRID = "#0b0b0b", "#52514e", "#e4e3df"
plt.rcParams.update({"font.family": "serif", "font.size": 8, "pdf.fonttype": 42})


def style(ax):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.yaxis.grid(True, color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)


fig, ax = plt.subplots(figsize=(3.45, 2.5))
w = 0.26
for i, p in enumerate(("linear", "adaptive", "mixed")):
    v = S["policies"][p]["zone_by_tercile"]
    m = [v[str(k)][0] for k in range(3)]
    e = [[v[str(k)][0] - v[str(k)][1] for k in range(3)], [v[str(k)][2] - v[str(k)][0] for k in range(3)]]
    x = np.arange(3) + (i - 1) * (w + 0.02)
    ax.bar(x, m, w, color=COL[p], label=NAME[p], edgecolor="white", linewidth=0.8)
    ax.errorbar(x, m, yerr=e, fmt="none", ecolor=INK, elinewidth=0.8, capsize=2)
ax.set_xticks(range(3), ["Weak\nthird", "Middle\nthird", "Strong\nthird"])
ax.set_ylim(0, 1)
ax.set_ylabel("Share of attempts in zone")
style(ax)
ax.legend(frameon=False, fontsize=6.5, ncol=2, loc="lower center", bbox_to_anchor=(0.45, 1.0))
fig.tight_layout()
fig.savefig(OUT / "zone_by_tercile.pdf")

fig, ax = plt.subplots(figsize=(3.45, 2.1))
ks = [0.1, 0.2, 0.4, 0.8]
for p, mk, lab in (("adaptive", "o", "Adaptive selection"), ("random", "s", "Random selection")):
    d = S["k_calibration"][p]
    m = [d[str(k)]["rmse"][0] for k in ks]
    e = [[d[str(k)]["rmse"][0] - d[str(k)]["rmse"][1] for k in ks], [d[str(k)]["rmse"][2] - d[str(k)]["rmse"][0] for k in ks]]
    ax.errorbar(ks, m, yerr=e, marker=mk, markersize=4, linewidth=1.5, capsize=2, color=COL[p], label=lab)
ax.set_xscale("log", base=2)
ax.set_xticks(ks, [str(k) for k in ks])
ax.minorticks_off()
ax.set_xlabel("Student update step $K$")
ax.set_ylabel(r"RMSE of $\hat\theta$ (logits)")
style(ax)
ax.legend(frameon=False)
fig.tight_layout()
fig.savefig(OUT / "rmse_by_k.pdf")
