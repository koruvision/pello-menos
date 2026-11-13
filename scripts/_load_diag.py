# -*- coding: utf-8 -*-
"""Diagnose load-test errors at moderate concurrency on oficialteste."""
from __future__ import annotations

import collections
import concurrent.futures
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


BASE = read_env(ROOT / "projeto-migracao/.secrets/oficialteste.env")[
    "PM_OFICIALTESTE_URL"
].rstrip("/")
PATHS = ["/", "/masculino/", "/produto/axila-cera/", "/carrinho/", "/wp-content/uploads/pm-home/home.css"]


def one(url: str) -> tuple[str, int, str]:
    req = urllib.request.Request(url, headers={"User-Agent": "pm-load-diag/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            resp.read()
            return url, resp.status, "ok"
    except urllib.error.HTTPError as e:
        return url, e.code, f"http:{e.code}"
    except Exception as e:  # noqa: BLE001
        return url, 0, type(e).__name__ + ":" + str(e)[:80]


def run(workers: int, n: int) -> None:
    urls = [BASE + p for p in PATHS]
    counts: collections.Counter[str] = collections.Counter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        futs = [pool.submit(one, urls[i % len(urls)]) for i in range(n)]
        for f in concurrent.futures.as_completed(futs):
            _u, _s, kind = f.result()
            counts[kind] += 1
    print(f"workers={workers} n={n}", dict(counts))


if __name__ == "__main__":
    for w in (5, 10, 15, 20):
        run(w, w * 20)
        time.sleep(2)
