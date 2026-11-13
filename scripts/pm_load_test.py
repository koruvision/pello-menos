# -*- coding: utf-8 -*-
"""Bateria de carga GET-only (oficialteste ou loja com --permitir-loja).

Ramp: warm-up → 20 → 50 → 100 VUs equivalentes (workers concurrentes).
Aborta se taxa de erro >5% ou p95 HTML >8s.
Sem POST de checkout/pagamento.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import http.client
import socket
import ssl
import statistics
import sys
import time
import urllib.parse
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

DEFAULT_PATHS = [
    "/",
    "/masculino/",
    "/produto/axila-cera/",
    "/produto/plano-silver/",
    "/carrinho/",
    "/wp-content/uploads/pm-home/home.css",
    "/wp-content/uploads/pm-home/home.js",
]

# GET leve e pouco concorrente — nunca POST checkout
LIGHT_PATHS = [
    "/finalizar-pagamento/",
]


def read_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


@dataclass
class Sample:
    url: str
    ok: bool
    status: int
    elapsed_ms: float
    bytes: int = 0
    error: str = ""


@dataclass
class StageResult:
    name: str
    workers: int
    duration_s: float
    samples: list[Sample] = field(default_factory=list)

    @property
    def ok_count(self) -> int:
        return sum(1 for s in self.samples if s.ok)

    @property
    def err_rate(self) -> float:
        if not self.samples:
            return 0.0
        return 1 - (self.ok_count / len(self.samples))

    def latencies(self, html_only: bool = False) -> list[float]:
        out = []
        for s in self.samples:
            if not s.ok:
                continue
            if html_only and (
                s.url.endswith(".css")
                or s.url.endswith(".js")
                or "/wp-content/uploads/" in s.url
            ):
                continue
            out.append(s.elapsed_ms)
        return out


_IPV4_CACHE: dict[str, str] = {}


def resolve_ipv4(host: str) -> str:
    if host not in _IPV4_CACHE:
        infos = socket.getaddrinfo(host, 443, socket.AF_INET, socket.SOCK_STREAM)
        _IPV4_CACHE[host] = infos[0][4][0]
    return _IPV4_CACHE[host]


class _HTTPSConnectionIPv4(http.client.HTTPSConnection):
    """HTTPSConnection que resolve só A (IPv4) e mantém SNI no hostname."""

    def connect(self) -> None:
        ip = resolve_ipv4(self.host)
        sock = socket.create_connection((ip, self.port), self.timeout)
        context = self._context or ssl.create_default_context()
        self.sock = context.wrap_socket(sock, server_hostname=self.host)


def fetch(url: str, timeout: int = 30) -> Sample:
    """GET via IPv4 only — Hostinger IPv6 TLS falha neste ambiente (TLSV1_ALERT_INTERNAL_ERROR)."""
    started = time.perf_counter()
    parsed = urllib.parse.urlparse(url)
    host = parsed.hostname or ""
    path = parsed.path or "/"
    if parsed.query:
        path += "?" + parsed.query
    try:
        conn = _HTTPSConnectionIPv4(host, timeout=timeout, context=ssl.create_default_context())
        try:
            conn.request(
                "GET",
                path,
                headers={
                    "User-Agent": "pm-load-test/1.0 (+get-only)",
                    "Cache-Control": "no-cache",
                    "Accept": "*/*",
                    "Connection": "close",
                },
            )
            resp = conn.getresponse()
            body = resp.read()
            elapsed = (time.perf_counter() - started) * 1000
            ok = 200 <= resp.status < 400
            return Sample(
                url,
                ok,
                resp.status,
                elapsed,
                len(body),
                error="" if ok else f"http:{resp.status}",
            )
        finally:
            conn.close()
    except Exception as exc:  # noqa: BLE001
        elapsed = (time.perf_counter() - started) * 1000
        return Sample(url, False, 0, elapsed, error=f"{type(exc).__name__}:{exc}")


def run_stage(
    base: str,
    paths: list[str],
    workers: int,
    duration_s: float,
    name: str,
) -> StageResult:
    urls = [base.rstrip("/") + p for p in paths]
    result = StageResult(name=name, workers=workers, duration_s=duration_s)
    deadline = time.perf_counter() + duration_s
    idx = 0

    def one(url: str) -> Sample:
        return fetch(url)

    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        pending: set[concurrent.futures.Future] = set()
        while time.perf_counter() < deadline or pending:
            while time.perf_counter() < deadline and len(pending) < workers:
                url = urls[idx % len(urls)]
                idx += 1
                pending.add(pool.submit(one, url))
            if not pending:
                break
            done, pending = concurrent.futures.wait(
                pending, timeout=0.25, return_when=concurrent.futures.FIRST_COMPLETED
            )
            for fut in done:
                result.samples.append(fut.result())
    return result


def pct(values: list[float], p: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    k = min(len(ordered) - 1, max(0, int(round((p / 100) * (len(ordered) - 1)))))
    return ordered[k]


def summarize(stage: StageResult) -> dict:
    all_lat = [s.elapsed_ms for s in stage.samples if s.ok]
    html_lat = stage.latencies(html_only=True)
    elapsed = stage.duration_s
    rps = len(stage.samples) / elapsed if elapsed else 0
    return {
        "name": stage.name,
        "workers": stage.workers,
        "requests": len(stage.samples),
        "ok": stage.ok_count,
        "err_rate": round(stage.err_rate * 100, 2),
        "rps": round(rps, 2),
        "p50_ms": round(pct(all_lat, 50) or 0, 1),
        "p95_ms": round(pct(all_lat, 95) or 0, 1),
        "p95_html_ms": round(pct(html_lat, 95) or 0, 1),
        "mean_ms": round(statistics.mean(all_lat), 1) if all_lat else 0,
    }


def write_report(path: Path, base: str, stages: list[dict], aborted: str | None, label: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    lines = [
        f"# Carga {label} (GET-only)",
        "",
        f"- Gerado em: `{now}` (UTC)",
        f"- Destino: `{base}`",
        "- Método: GET concorrente (http.client + ThreadPoolExecutor, **somente IPv4**); **sem POST** checkout/pagamento",
        "- Alvos: `/`, `/masculino/`, 2 PDPs, `/carrinho/`, `home.css`/`home.js`; `/finalizar-pagamento/` só no warm-up leve",
        "- Nota: resolução AAAA/IPv6 neste host devolveu `TLSV1_ALERT_INTERNAL_ERROR` e inflava erro; teste força IPv4 + SNI.",
        "",
        "## Resultados por degrau",
        "",
        "| Degrau | Workers | Reqs | OK | Err% | RPS | p50 ms | p95 ms | p95 HTML ms |",
        "|--------|---------|------|----|------|-----|--------|--------|-------------|",
    ]
    for s in stages:
        lines.append(
            f"| `{s['name']}` | {s['workers']} | {s['requests']} | {s['ok']} | {s['err_rate']} | "
            f"{s['rps']} | {s['p50_ms']} | {s['p95_ms']} | {s['p95_html_ms']} |"
        )
    lines += ["", "## Critérios de abort"]
    lines.append("- Erro > 5% ou p95 HTML > 8000 ms → abort")
    if aborted:
        lines.append(f"- **Abortado:** {aborted}")
        stable = [s for s in stages if s["name"] != aborted.split(":")[0]]
        if stable:
            last = stable[-1]
            lines.append(
                f"- **Capacidade segura (último estável):** `{last['name']}` "
                f"({last['workers']} workers, p95 HTML {last['p95_html_ms']} ms, err {last['err_rate']}%)"
            )
    else:
        lines.append("- Não abortado; bateria completa.")
        if stages:
            last = stages[-1]
            lines.append(
                f"- **Capacidade observada:** até `{last['name']}` "
                f"({last['workers']} workers) sem estouro dos critérios."
            )
    lines += [
        "",
        "## Notas",
        "",
        "- Checkout/pagamento: fora do stress (apenas GET leve no warm-up, baixa concorrência).",
        "- Não inclui sessão Woo autenticada nem Store API write.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")
    print("report", path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--env", required=True)
    parser.add_argument("--prefix", default="PM_OFICIALTESTE")
    parser.add_argument("--permitir-loja", action="store_true")
    parser.add_argument("--stage-seconds", type=float, default=45.0)
    parser.add_argument("--warmup-seconds", type=float, default=30.0)
    parser.add_argument(
        "--report",
        default="",
        help="path do markdown de saída",
    )
    args = parser.parse_args()

    env = read_env(Path(args.env))
    base = env[f"{args.prefix}_URL"].rstrip("/")
    is_loja = "loja.pellomenos.com.br" in base
    if is_loja and not args.permitir_loja:
        sys.exit("recusado: destino é a loja oficial (passe --permitir-loja)")

    label = "loja" if is_loja else "oficialteste"
    stages_cfg = [
        ("warmup", 5, args.warmup_seconds, DEFAULT_PATHS + LIGHT_PATHS),
        ("vu20", 20, args.stage_seconds, DEFAULT_PATHS),
        ("vu50", 50, args.stage_seconds, DEFAULT_PATHS),
        ("vu100", 100, args.stage_seconds, DEFAULT_PATHS),
    ]

    summaries: list[dict] = []
    aborted: str | None = None
    for name, workers, dur, paths in stages_cfg:
        print(f"== {name} workers={workers} duration={dur}s ==")
        stage = run_stage(base, paths, workers, dur, name)
        summary = summarize(stage)
        summaries.append(summary)
        print(summary)
        if summary["err_rate"] > 5:
            aborted = f"{name}: err_rate {summary['err_rate']}% > 5%"
            break
        if summary["p95_html_ms"] > 8000:
            aborted = f"{name}: p95_html {summary['p95_html_ms']} ms > 8000"
            break

    out = Path(args.report) if args.report else (
        ROOT / "projeto-migracao" / "historico" / (
            "22-carga-loja.md" if is_loja else "19-carga-oficialteste.md"
        )
    )
    write_report(out, base, summaries, aborted, label)
    if aborted:
        print("ABORTED", aborted)
        sys.exit(2)


if __name__ == "__main__":
    main()
