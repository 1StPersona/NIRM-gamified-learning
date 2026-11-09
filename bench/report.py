"""Сводка и графики по результатам нагрузочного теста: python -m bench.report"""
import csv
from collections import defaultdict
from statistics import mean, stdev

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

rows = list(csv.DictReader(open("bench/results/load.csv")))
agg = defaultdict(list)
for r in rows:
    agg[(r["store"], int(r["concurrency"]))].append(r)

lines = ["| Хранилище | Клиентов | Пропускная способность, запр/с (ср. ± СКО) | p50, мс | p95, мс | p99, мс | Ошибки |",
         "| --- | --- | --- | --- | --- | --- | --- |"]
series = defaultdict(lambda: ([], [], [], []))
for (store, c), rs in sorted(agg.items()):
    thr = [float(r["throughput_rps"]) for r in rs]
    m = lambda k: mean(float(r[k]) for r in rs)
    lines.append(f"| {store} | {c} | {mean(thr):.0f} ± {stdev(thr):.0f} | {m('p50_ms'):.1f} | {m('p95_ms'):.1f} | {m('p99_ms'):.1f} | {sum(int(r['errors']) for r in rs)} |")
    s = series[store]; s[0].append(c); s[1].append(mean(thr)); s[2].append(stdev(thr)); s[3].append(m("p95_ms"))
open("bench/results/load_summary.md", "w").write("\n".join(lines) + "\n")
print("\n".join(lines))

fig, (a1, a2) = plt.subplots(1, 2, figsize=(10, 4))
for store, (c, thr, sd, p95) in series.items():
    a1.errorbar(c, thr, yerr=sd, marker="o", capsize=4, label=store)
    a2.plot(c, p95, marker="o", label=store)
a1.set(xscale="log", xlabel="Одновременных клиентов", ylabel="Запросов в секунду", title="Пропускная способность")
a2.set(xscale="log", yscale="log", xlabel="Одновременных клиентов", ylabel="p95 задержки, мс", title="Задержка (95-й перцентиль)")
for a in (a1, a2):
    a.set_xticks([1, 8, 32, 64]); a.set_xticklabels(["1", "8", "32", "64"]); a.grid(alpha=.3); a.legend()
fig.tight_layout(); fig.savefig("bench/plots/load.png", dpi=150)
