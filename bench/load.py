"""Нагрузочный тест сервиса геймификации (макробенчмарк, лекция 8).

Замкнутая модель нагрузки: C виртуальных клиентов шлют события «решение проверено»
без пауз. Каждый прогон: прогрев W секунд (не учитывается) + замер D секунд.
Пример: python -m bench.load --url http://127.0.0.1:8000 --concurrency 1 8 32 64 --reps 3
"""
from __future__ import annotations

import argparse
import asyncio
import csv
import random
import time
from concurrent.futures import ProcessPoolExecutor

import aiohttp
import numpy as np


async def worker(client: aiohttp.ClientSession, url: str, stop_at: float, measure_from: float,
                 lat: list[float], errors: list[int], rng: random.Random) -> None:
    while (now := time.perf_counter()) < stop_at:
        ev = {"user_id": f"u{rng.randrange(1000)}", "task_id": f"q{rng.randrange(50):02d}",
              "solved": rng.random() < 0.7, "attempts": rng.randint(1, 3)}
        t0 = time.perf_counter()
        try:
            async with client.post(url + "/events/submission", json=ev) as r:
                await r.read()
                ok = r.status == 200
        except aiohttp.ClientError:
            ok = False
        t1 = time.perf_counter()
        if t0 >= measure_from:
            (lat.append(t1 - t0) if ok else errors.append(1))


async def client_proc(url: str, c: int, warmup: float, duration: float, seed: int) -> tuple[list[float], int]:
    lat: list[float] = []
    errors: list[int] = []
    conn = aiohttp.TCPConnector(limit=c)
    async with aiohttp.ClientSession(connector=conn, timeout=aiohttp.ClientTimeout(total=10)) as client:
        start = time.perf_counter()
        measure_from, stop_at = start + warmup, start + warmup + duration
        await asyncio.gather(*(worker(client, url, stop_at, measure_from, lat, errors, random.Random(seed + i))
                               for i in range(c)))
    return lat, len(errors)


def _proc_entry(args: tuple) -> tuple[list[float], int]:
    return asyncio.run(client_proc(*args))


def run(url: str, c: int, warmup: float, duration: float, seed: int, procs: int) -> dict:
    """Клиенты распределяются по procs процессам: один процесс Python упирается в CPU
    раньше сервера и искажает результат при большой конкуренции."""
    procs = max(1, min(procs, c))
    shares = [c // procs + (1 if i < c % procs else 0) for i in range(procs)]
    with ProcessPoolExecutor(procs) as ex:
        parts = list(ex.map(_proc_entry, [(url, n, warmup, duration, seed + 100 * i) for i, n in enumerate(shares)]))
    lat = [x for p in parts for x in p[0]]
    errors = [1] * sum(p[1] for p in parts)
    a = np.array(lat) * 1000
    return {"concurrency": c, "requests": len(a), "errors": len(errors),
            "throughput_rps": round(len(a) / duration, 1),
            "p50_ms": round(float(np.percentile(a, 50)), 2), "p95_ms": round(float(np.percentile(a, 95)), 2),
            "p99_ms": round(float(np.percentile(a, 99)), 2)}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://127.0.0.1:8000")
    ap.add_argument("--label", default="memory")
    ap.add_argument("--concurrency", type=int, nargs="+", default=[1, 8, 32, 64])
    ap.add_argument("--reps", type=int, default=3)
    ap.add_argument("--warmup", type=float, default=2.0)
    ap.add_argument("--duration", type=float, default=10.0)
    ap.add_argument("--procs", type=int, default=2, help="процессов-генераторов нагрузки")
    ap.add_argument("--out", default="bench/results/load.csv")
    a = ap.parse_args()
    rows = []
    for c in a.concurrency:
        for rep in range(a.reps):
            r = run(a.url, c, a.warmup, a.duration, 1000 * rep, a.procs)
            r.update(store=a.label, rep=rep, procs=a.procs)
            rows.append(r)
            print(r, flush=True)
    new = not __import__("os").path.exists(a.out)
    with open(a.out, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        if new:
            w.writeheader()
        w.writerows(rows)


if __name__ == "__main__":
    main()
