# -*- coding: utf-8 -*-
"""Baseline PageSpeed Insights + inventário de bytes (read-only).

Uso:
  python scripts/pm_psi_audit.py --env projeto-migracao/.secrets/oficialteste.env
  python scripts/pm_psi_audit.py --env projeto-migracao/.secrets/loja.env --prefix PM_LOJA --permitir-loja --runs 1
  python scripts/pm_psi_audit.py --env ... --skip-psi   # só inventário de assets

Não altera checkout nem publica nada. Chave: PM_PAGESPEED_API_KEY no .env (ou no ambiente).
"""
from __future__ import annotations

import argparse
import http.client
import json
import socket
import ssl
import statistics
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

_IPV4_CACHE: dict[str, str] = {}


def _resolve_ipv4(host: str) -> str:
    if host not in _IPV4_CACHE:
        infos = socket.getaddrinfo(host, 443, socket.AF_INET, socket.SOCK_STREAM)
        _IPV4_CACHE[host] = infos[0][4][0]
    return _IPV4_CACHE[host]


class _HTTPSConnectionIPv4(http.client.HTTPSConnection):
    def connect(self) -> None:
        ip = _resolve_ipv4(self.host)
        sock = socket.create_connection((ip, self.port), self.timeout)
        context = self._context or ssl.create_default_context()
        self.sock = context.wrap_socket(sock, server_hostname=self.host)

ROOT = Path(__file__).resolve().parents[1]
PSI_API = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"

DEFAULT_PATHS = [
    ("/", "home-fem"),
    ("/masculino/", "home-masc"),
    ("/produto/axila-cera/", "pdp-cera"),
    ("/produto/axilas-laser/", "pdp-laser"),
    ("/carrinho/", "carrinho"),
    ("/finalizar-pagamento/", "checkout-get-only"),
]

CRITICAL_ASSETS = [
    "/wp-content/uploads/pm-home/home.js",
    "/wp-content/uploads/pm-home/home.css",
    "/wp-content/uploads/pm-home/cart.js",
    "/wp-content/uploads/pm-home/product.js",
    "/wp-content/uploads/pm-home/whatsapp-float.js",
    "/wp-content/uploads/pm-home/checkout-shell-c24.js",
    "/wp-content/uploads/pm-home/checkout-loading.js",
    "/wp-content/uploads/pm-home/checkout-brand.css",
    "https://cdn.jsdelivr.net/npm/gsap@3.15.0/dist/gsap.min.js",
    "https://cdn.jsdelivr.net/npm/gsap@3.15.0/dist/ScrollTrigger.min.js",
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


def http_probe(url: str, timeout: int = 60) -> dict:
    """GET probe via IPv4 (evita TLSV1_ALERT_INTERNAL_ERROR no AAAA deste host)."""
    started = time.perf_counter()
    parsed = urllib.parse.urlparse(url)
    host = parsed.hostname or ""
    path = parsed.path or "/"
    if parsed.query:
        path += "?" + parsed.query
    try:
        if parsed.scheme == "https":
            conn = _HTTPSConnectionIPv4(
                host, timeout=timeout, context=ssl.create_default_context()
            )
        else:
            conn = http.client.HTTPConnection(host, timeout=timeout)
        try:
            conn.request(
                "GET",
                path,
                headers={"User-Agent": "pm-psi-audit/1.0", "Cache-Control": "no-cache"},
            )
            resp = conn.getresponse()
            body = resp.read()
            headers = {k.lower(): v for k, v in resp.getheaders()}
            elapsed_ms = round((time.perf_counter() - started) * 1000, 1)
            return {
                "url": url,
                "ok": 200 <= resp.status < 400,
                "status": resp.status,
                "bytes": len(body),
                "elapsed_ms": elapsed_ms,
                "content_type": headers.get("content-type", ""),
                "cache_control": headers.get("cache-control", ""),
                "content_encoding": headers.get("content-encoding", ""),
            }
        finally:
            conn.close()
    except Exception as exc:  # noqa: BLE001 — reportar falha medida
        elapsed_ms = round((time.perf_counter() - started) * 1000, 1)
        return {
            "url": url,
            "ok": False,
            "error": str(exc),
            "elapsed_ms": elapsed_ms,
            "bytes": 0,
        }


def extract_pm_home_urls(html: str, origin: str) -> list[str]:
    needle = origin.rstrip("/") + "/wp-content/uploads/pm-home/"
    found: list[str] = []
    start = 0
    while True:
        i = html.find(needle, start)
        if i < 0:
            break
        j = i
        while j < len(html) and html[j] not in "\"' )> \t\n\r":
            j += 1
        url = html[i:j].rstrip("\\")
        if url not in found:
            found.append(url)
        start = j
    return found


def psi_run(api_key: str, page_url: str, strategy: str) -> dict:
    params = urllib.parse.urlencode(
        {
            "url": page_url,
            "key": api_key,
            "strategy": strategy,
            "category": "performance",
        }
    )
    req = urllib.request.Request(
        PSI_API + "?" + params,
        headers={"User-Agent": "pm-psi-audit/1.0"},
    )
    with urllib.request.urlopen(req, timeout=180) as resp:
        return json.loads(resp.read().decode("utf-8"))


def metric_ms(audits: dict, key: str):
    node = audits.get(key) or {}
    val = node.get("numericValue")
    if val is None:
        return None
    return round(float(val), 1)


def summarize_psi(payload: dict) -> dict:
    lh = payload.get("lighthouseResult") or {}
    cats = lh.get("categories") or {}
    audits = lh.get("audits") or {}
    perf = (cats.get("performance") or {}).get("score")
    opportunities = []
    for audit_id, audit in audits.items():
        if audit.get("details", {}).get("type") != "opportunity":
            continue
        savings = (audit.get("details") or {}).get("overallSavingsMs")
        if not savings:
            continue
        opportunities.append(
            {
                "id": audit_id,
                "title": audit.get("title"),
                "savings_ms": round(float(savings), 1),
                "display": audit.get("displayValue"),
            }
        )
    opportunities.sort(key=lambda x: x["savings_ms"], reverse=True)

    diagnostics = []
    for audit_id in (
        "unused-javascript",
        "unused-css-rules",
        "render-blocking-resources",
        "total-byte-weight",
        "mainthread-work-breakdown",
        "bootup-time",
        "dom-size",
        "legacy-javascript",
        "uses-long-cache-ttl",
        "efficient-animated-content",
        "modern-image-formats",
        "uses-optimized-images",
        "uses-responsive-images",
        "offscreen-images",
    ):
        audit = audits.get(audit_id)
        if not audit:
            continue
        diagnostics.append(
            {
                "id": audit_id,
                "title": audit.get("title"),
                "score": audit.get("score"),
                "display": audit.get("displayValue"),
                "savings_ms": (audit.get("details") or {}).get("overallSavingsMs"),
                "savings_bytes": (audit.get("details") or {}).get("overallSavingsBytes"),
            }
        )

    lcp_el = None
    lcp_audit = audits.get("largest-contentful-paint-element") or {}
    items = (lcp_audit.get("details") or {}).get("items") or []
    if items:
        lcp_el = items[0]

    return {
        "performance_score": None if perf is None else round(float(perf) * 100),
        "fcp_ms": metric_ms(audits, "first-contentful-paint"),
        "lcp_ms": metric_ms(audits, "largest-contentful-paint"),
        "tbt_ms": metric_ms(audits, "total-blocking-time"),
        "cls": None
        if audits.get("cumulative-layout-shift", {}).get("numericValue") is None
        else round(float(audits["cumulative-layout-shift"]["numericValue"]), 3),
        "si_ms": metric_ms(audits, "speed-index"),
        "tti_ms": metric_ms(audits, "interactive"),
        "inp_ms": metric_ms(audits, "interaction-to-next-paint"),
        "total_byte_weight": (audits.get("total-byte-weight") or {}).get("numericValue"),
        "lcp_element": lcp_el,
        "opportunities": opportunities[:12],
        "diagnostics": diagnostics,
        "final_url": lh.get("finalDisplayedUrl") or lh.get("requestedUrl"),
        "fetch_time": lh.get("fetchTime"),
    }


def median_summaries(rows: list[dict]) -> dict:
    if not rows:
        return {}
    out = {"runs": len(rows)}
    for key in (
        "performance_score",
        "fcp_ms",
        "lcp_ms",
        "tbt_ms",
        "cls",
        "si_ms",
        "tti_ms",
        "inp_ms",
        "total_byte_weight",
    ):
        vals = [r[key] for r in rows if r.get(key) is not None]
        if not vals:
            out[key] = None
        elif key == "cls":
            out[key] = round(statistics.median(vals), 3)
        elif key == "performance_score":
            out[key] = int(round(statistics.median(vals)))
        else:
            out[key] = round(statistics.median(vals), 1)
    # keep richest opportunity set from best-documented run (last)
    out["opportunities"] = rows[-1].get("opportunities") or []
    out["diagnostics"] = rows[-1].get("diagnostics") or []
    out["lcp_element"] = rows[-1].get("lcp_element")
    out["final_url"] = rows[-1].get("final_url")
    return out


def fmt_bytes(n) -> str:
    if n is None:
        return "—"
    n = float(n)
    if n >= 1_000_000:
        return f"{n/1_000_000:.2f} MB"
    if n >= 1000:
        return f"{n/1000:.1f} KB"
    return f"{int(n)} B"


def write_report(path: Path, meta: dict, psi: dict, assets: dict, page_probes: dict) -> None:
    lines: list[str] = []
    is_loja = "loja.pellomenos.com.br" in (meta.get("base") or "")
    title = (
        "# 23 — Baseline PageSpeed Insights (loja)"
        if is_loja
        else "# 17 — Baseline PageSpeed Insights (oficialteste)"
    )
    json_dir = "psi-loja" if is_loja else "psi-oficialteste"
    lines.append(title)
    lines.append("")
    lines.append(f"- Gerado em: `{meta['generated_at']}` (UTC)")
    lines.append(f"- Destino: `{meta['base']}`")
    lines.append(f"- Corridas por URL/estratégia: `{meta['runs']}` (mediana)")
    lines.append("- Fonte: Google PageSpeed Insights API v5 + GET medido dos assets")
    lines.append("- Checkout: `/finalizar-pagamento/` medido só em GET; **zero alteração de código**")
    lines.append("- Chave PSI: variável `PM_PAGESPEED_API_KEY` (não versionada)")
    lines.append("")
    lines.append("## Resumo scores (mediana)")
    lines.append("")
    lines.append("| Página | Mobile | Desktop | LCP mobile (ms) | TBT mobile (ms) | CLS mobile | Bytes total (PSI mobile) |")
    lines.append("|--------|--------|---------|-----------------|-----------------|------------|--------------------------|")
    for slug, _path in meta["paths"]:
        m = (psi.get(slug) or {}).get("mobile") or {}
        d = (psi.get(slug) or {}).get("desktop") or {}
        lines.append(
            f"| `{slug}` | {m.get('performance_score', '—')} | {d.get('performance_score', '—')} | "
            f"{m.get('lcp_ms', '—')} | {m.get('tbt_ms', '—')} | {m.get('cls', '—')} | "
            f"{fmt_bytes(m.get('total_byte_weight'))} |"
        )
    lines.append("")

    for slug, route in meta["paths"]:
        lines.append(f"## `{slug}` (`{route}`)")
        lines.append("")
        probe = page_probes.get(slug) or {}
        if probe:
            lines.append(
                f"- HTML GET medido: **{fmt_bytes(probe.get('bytes'))}** em **{probe.get('elapsed_ms')} ms** "
                f"(HTTP {probe.get('status')})"
            )
            lines.append("")
        for strategy in ("mobile", "desktop"):
            s = (psi.get(slug) or {}).get(strategy) or {}
            if not s:
                lines.append(f"### {strategy}: sem dados")
                lines.append("")
                continue
            lines.append(f"### {strategy} (mediana de {s.get('runs', '?')} run(s))")
            lines.append("")
            lines.append("| Métrica | Valor |")
            lines.append("|---------|-------|")
            lines.append(f"| Performance score | {s.get('performance_score')} |")
            lines.append(f"| FCP (ms) | {s.get('fcp_ms')} |")
            lines.append(f"| LCP (ms) | {s.get('lcp_ms')} |")
            lines.append(f"| TBT (ms) | {s.get('tbt_ms')} |")
            lines.append(f"| CLS | {s.get('cls')} |")
            lines.append(f"| Speed Index (ms) | {s.get('si_ms')} |")
            lines.append(f"| TTI (ms) | {s.get('tti_ms')} |")
            lines.append(f"| INP (ms) | {s.get('inp_ms')} |")
            lines.append(f"| Total byte weight | {fmt_bytes(s.get('total_byte_weight'))} |")
            lines.append("")
            if s.get("lcp_element"):
                lines.append(f"- LCP element (última run): `{json.dumps(s['lcp_element'], ensure_ascii=False)[:500]}`")
                lines.append("")
            opps = s.get("opportunities") or []
            if opps:
                lines.append("Oportunidades PSI (savings_ms):")
                lines.append("")
                for op in opps[:8]:
                    lines.append(
                        f"- **{op.get('title')}** (`{op.get('id')}`): {op.get('savings_ms')} ms"
                        + (f" — {op.get('display')}" if op.get("display") else "")
                    )
                lines.append("")
            diags = s.get("diagnostics") or []
            interesting = [
                d
                for d in diags
                if d.get("score") is not None and d.get("score") < 1
            ]
            if interesting:
                lines.append("Diagnósticos com score < 1:")
                lines.append("")
                for d in interesting:
                    extra = []
                    if d.get("display"):
                        extra.append(str(d["display"]))
                    if d.get("savings_bytes"):
                        extra.append(f"savings {fmt_bytes(d['savings_bytes'])}")
                    if d.get("savings_ms"):
                        extra.append(f"{round(float(d['savings_ms']), 1)} ms")
                    lines.append(
                        f"- `{d.get('id')}` score={d.get('score')} — {d.get('title')}"
                        + (f" ({'; '.join(extra)})" if extra else "")
                    )
                lines.append("")

    lines.append("## Inventário de assets críticos (GET no oficialteste)")
    lines.append("")
    lines.append("| Asset | Bytes | ms | Status | Cache-Control | Encoding |")
    lines.append("|-------|------:|---:|-------:|---------------|----------|")
    for row in assets.get("critical") or []:
        lines.append(
            f"| `{row.get('url', '')}` | {row.get('bytes', 0)} | {row.get('elapsed_ms', '—')} | "
            f"{row.get('status', row.get('error', '—'))} | `{row.get('cache_control', '')}` | "
            f"`{row.get('content_encoding', '')}` |"
        )
    lines.append("")

    home_assets = assets.get("home_pm_home") or []
    if home_assets:
        total = sum(r.get("bytes") or 0 for r in home_assets if r.get("ok"))
        lines.append("## Assets `pm-home` referenciados na home (GET medido)")
        lines.append("")
        lines.append(f"- Contagem URLs distintas: **{len(home_assets)}**")
        lines.append(f"- Soma dos bytes OK: **{fmt_bytes(total)}**")
        lines.append("")
        lines.append("| Bytes | ms | URL |")
        lines.append("|------:|---:|-----|")
        ranked = sorted(
            [r for r in home_assets if r.get("ok")],
            key=lambda r: r.get("bytes") or 0,
            reverse=True,
        )
        for row in ranked[:40]:
            lines.append(
                f"| {row.get('bytes')} | {row.get('elapsed_ms')} | `{row.get('url')}` |"
            )
        if len(ranked) > 40:
            lines.append(f"| … | … | (+{len(ranked) - 40} omitidos; ver JSON) |")
        lines.append("")

    lines.append("## Black Friday — leitura só dos números acima")
    lines.append("")
    lines.append("- Gargalos = linhas com pior LCP/TBT/score e oportunidades PSI com maior `savings_ms`.")
    lines.append("- **Não tocar agora:** checkout CF7 #1831, Accesstage, `checkout-shell*.js`, fluxo de pagamento.")
    lines.append(
        "- Capacidade de host/CDN: ver runbook de migração "
        "(`historico/12-cronograma-loja-oficial.md`); este relatório não estima RPS do servidor."
    )
    lines.append("")

    lines.append("## Remediações candidatas (NÃO aplicadas — aguardam GO)")
    lines.append("")
    lines.append(
        "Cada item abaixo só entra em execução se citado por PSI/inventário nesta baseline; "
        "nenhum foi aplicado neste passo."
    )
    lines.append("")
    # Fill candidates from measured data
    opp_ids: set = set()
    diag_ids: set = set()
    for slug in psi:
        for strategy in ("mobile", "desktop"):
            block = (psi.get(slug) or {}).get(strategy) or {}
            opp_ids |= {o.get("id") for o in (block.get("opportunities") or [])}
            diag_ids |= {
                d.get("id")
                for d in (block.get("diagnostics") or [])
                if d.get("score") is not None and d.get("score") < 1
            }
    candidates = []
    if "modern-image-formats" in opp_ids or "modern-image-formats" in diag_ids or "uses-optimized-images" in opp_ids or "uses-optimized-images" in diag_ids:
        candidates.append(
            "Imagens: formatos modernos / compressão (PSI `modern-image-formats` / `uses-optimized-images`) — só mídia `pm-home`, fora checkout."
        )
    if "uses-responsive-images" in opp_ids or "uses-responsive-images" in diag_ids:
        candidates.append(
            "Imagens responsivas / `srcset` (PSI `uses-responsive-images`) nas vitrines da home/PDP."
        )
    if "offscreen-images" in opp_ids or "offscreen-images" in diag_ids:
        candidates.append(
            "Lazy-load de imagens below-the-fold (PSI `offscreen-images`)."
        )
    if "unused-javascript" in opp_ids or "unused-javascript" in diag_ids:
        candidates.append(
            "JS não usado (PSI `unused-javascript`): auditar GSAP/ScrollTrigger/GTM na home — **sem** remover scripts de checkout."
        )
    if "render-blocking-resources" in opp_ids or "render-blocking-resources" in diag_ids:
        candidates.append(
            "CSS/JS render-blocking (PSI `render-blocking-resources`): `home.css` / ordem de carga — mudança mínima."
        )
    if "uses-long-cache-ttl" in diag_ids:
        candidates.append(
            "Cache-Control curto em estáticos `pm-home` (PSI `uses-long-cache-ttl`) — header no host/CDN, não código de checkout."
        )
    html_bytes = (page_probes.get("home-fem") or {}).get("bytes") or 0
    if html_bytes > 300_000:
        candidates.append(
            f"HTML da home medido em {fmt_bytes(html_bytes)}: avaliar redução de markup exportado (fora checkout)."
        )
    checkout_m = (psi.get("checkout-get-only") or {}).get("mobile") or {}
    if checkout_m.get("performance_score") is not None and checkout_m.get("performance_score") < 60:
        candidates.append(
            f"Checkout GET medido score mobile mediana {checkout_m.get('performance_score')} / LCP {checkout_m.get('lcp_ms')} ms — **somente observação**; remediação de checkout fora de escopo até GO explícito."
        )
    gsap = next((r for r in (assets.get("critical") or []) if "gsap.min.js" in (r.get("url") or "")), None)
    st = next(
        (r for r in (assets.get("critical") or []) if "ScrollTrigger" in (r.get("url") or "")),
        None,
    )
    if gsap and gsap.get("ok"):
        candidates.append(
            f"GSAP CDN medido {fmt_bytes(gsap.get('bytes'))}"
            + (f" + ScrollTrigger {fmt_bytes(st.get('bytes'))}" if st and st.get("ok") else "")
            + ": carregar só onde animações existem (candidato; re-medir após)."
        )
    if not candidates:
        candidates.append(
            "Nenhuma oportunidade óbvia cruzada automaticamente — revisar tabelas PSI acima antes de qualquer patch."
        )
    for i, c in enumerate(candidates, 1):
        lines.append(f"{i}. {c}")
    lines.append("")
    lines.append("## Artefatos")
    lines.append("")
    lines.append(f"- JSON bruto: `projeto-migracao/.secrets/{json_dir}/` (gitignored)")
    lines.append("- Limpeza BD pós-migração: `historico/18-limpeza-bd-pos-migracao.md`")
    lines.append("")

    report_path = Path(path) if not isinstance(path, Path) else path
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--env", required=True)
    parser.add_argument("--prefix", default="PM_OFICIALTESTE")
    parser.add_argument("--permitir-loja", action="store_true")
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("--skip-psi", action="store_true")
    parser.add_argument(
        "--out-dir",
        default="",
    )
    parser.add_argument(
        "--report",
        default="",
    )
    parser.add_argument(
        "--slugs",
        default="",
        help="lista separada por vírgula (ex.: home-fem,carrinho); vazio = todas",
    )
    parser.add_argument(
        "--strategies",
        default="mobile,desktop",
        help="ex.: mobile  ou  mobile,desktop",
    )
    args = parser.parse_args()

    env = read_env(Path(args.env))
    base = (env.get(f"{args.prefix}_URL") or env.get("PM_OFICIALTESTE_URL") or "").rstrip("/")
    if not base:
        sys.exit(f"falta {args.prefix}_URL")
    is_loja = "loja.pellomenos.com.br" in base
    if is_loja and not args.permitir_loja:
        sys.exit("destino loja oficial bloqueado (passe --permitir-loja)")

    api_key = env.get("PM_PAGESPEED_API_KEY") or ""
    if not api_key:
        # permite chave só no oficialteste.env / ambiente do processo
        ot = ROOT / "projeto-migracao" / ".secrets" / "oficialteste.env"
        if ot.is_file():
            api_key = read_env(ot).get("PM_PAGESPEED_API_KEY") or ""
    import os

    api_key = os.environ.get("PM_PAGESPEED_API_KEY") or api_key

    out_dir = Path(
        args.out_dir
        or (
            ROOT / "projeto-migracao" / ".secrets" / ("psi-loja" if is_loja else "psi-oficialteste")
        )
    )
    out_dir.mkdir(parents=True, exist_ok=True)
    if not args.report:
        args.report = str(
            ROOT
            / "projeto-migracao"
            / "historico"
            / ("23-psi-loja-baseline.md" if is_loja else "17-psi-oficialteste-baseline.md")
        )

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    slug_filter = {s.strip() for s in args.slugs.split(",") if s.strip()}
    paths = [
        (path, slug)
        for path, slug in DEFAULT_PATHS
        if not slug_filter or slug in slug_filter
    ]
    strategies = [s.strip() for s in args.strategies.split(",") if s.strip()]

    print("destino:", base)
    print("inventário de páginas…")
    page_probes: dict[str, dict] = {}
    home_html = ""
    for path, slug in paths:
        url = base + path
        probe = http_probe(url)
        page_probes[slug] = probe
        print(f"  page {slug}: {probe.get('status')} {probe.get('bytes')} B {probe.get('elapsed_ms')} ms")
        if slug == "home-fem" and probe.get("ok"):
            # re-fetch via IPv4 for URL extraction
            parsed = urllib.parse.urlparse(url)
            conn = _HTTPSConnectionIPv4(
                parsed.hostname or "",
                timeout=60,
                context=ssl.create_default_context(),
            )
            try:
                conn.request("GET", parsed.path or "/", headers={"User-Agent": "pm-psi-audit/1.0"})
                resp = conn.getresponse()
                home_html = resp.read().decode("utf-8", "replace")
            finally:
                conn.close()

    print("assets críticos…")
    critical_rows = []
    for asset in CRITICAL_ASSETS:
        url = asset if asset.startswith("http") else base + asset
        row = http_probe(url)
        critical_rows.append(row)
        print(f"  asset {row.get('bytes')} B {row.get('elapsed_ms')} ms {url[-60:]}")

    home_asset_rows = []
    if home_html:
        urls = extract_pm_home_urls(home_html, base)
        print(f"pm-home refs na home: {len(urls)}")
        for i, url in enumerate(urls, 1):
            row = http_probe(url, timeout=90)
            home_asset_rows.append(row)
            if i % 20 == 0 or i == len(urls):
                print(f"  … {i}/{len(urls)}")

    assets_payload = {
        "critical": critical_rows,
        "home_pm_home": home_asset_rows,
        "home_pm_home_count": len(home_asset_rows),
        "home_pm_home_bytes_ok": sum(
            r.get("bytes") or 0 for r in home_asset_rows if r.get("ok")
        ),
    }
    (out_dir / f"assets-{stamp}.json").write_text(
        json.dumps(assets_payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (out_dir / f"pages-{stamp}.json").write_text(
        json.dumps(page_probes, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    psi_results: dict = {}
    if not args.skip_psi:
        if not api_key:
            sys.exit("falta PM_PAGESPEED_API_KEY no .env")
        for path, slug in paths:
            page_url = base + path
            psi_results[slug] = {}
            for strategy in strategies:
                runs = []
                for n in range(1, args.runs + 1):
                    print(f"PSI {slug} {strategy} run {n}/{args.runs}…")
                    try:
                        raw = psi_run(api_key, page_url, strategy)
                    except urllib.error.HTTPError as err:
                        body = err.read().decode("utf-8", "replace")[:800]
                        print("  HTTP", err.code, body)
                        time.sleep(5)
                        continue
                    except Exception as exc:  # noqa: BLE001
                        print("  ERR", exc)
                        time.sleep(5)
                        continue
                    raw_path = out_dir / f"psi-{slug}-{strategy}-r{n}-{stamp}.json"
                    raw_path.write_text(
                        json.dumps(raw, ensure_ascii=False), encoding="utf-8"
                    )
                    summary = summarize_psi(raw)
                    runs.append(summary)
                    print(
                        f"  score={summary.get('performance_score')} "
                        f"LCP={summary.get('lcp_ms')} TBT={summary.get('tbt_ms')}"
                    )
                    # polite pacing for API quota
                    time.sleep(2)
                psi_results[slug][strategy] = median_summaries(runs)

        (out_dir / f"psi-summary-{stamp}.json").write_text(
            json.dumps(psi_results, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    else:
        print("PSI skipped")

    meta = {
        "generated_at": stamp,
        "base": base,
        "runs": args.runs if not args.skip_psi else 0,
        "paths": [(slug, path) for path, slug in paths],
    }
    write_report(Path(args.report), meta, psi_results, assets_payload, page_probes)
    print("report:", args.report)
    print("json dir:", out_dir)


if __name__ == "__main__":
    main()
