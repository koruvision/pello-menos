# -*- coding: utf-8 -*-
"""Mantem o ambiente de teste (pellomenosoficialteste) identico a producao.

Fonte de verdade: **loja.pellomenos.com.br** (leitura publica, sem credencial).
O repositorio serve apenas como *manifesto* de quais arquivos existem, porque o
WordPress nao expoe listagem de diretorio.

Etapas:
  1. baixa da loja cada arquivo do manifesto (pm-home, sem media/fonts)
  2. envia para o teste em lotes (POST /wp-json/pm-home/v1/bundle)
  3. publica os snippets de wordpress-loja/snippets/ com o estado de producao
  4. verifica por hash: teste == loja

Credenciais do DESTINO: PM_SYNC_URL / PM_SYNC_USER / PM_SYNC_APP_PASSWORD
ou o .env local (padrao projeto-migracao/.secrets/oficialteste.env).

Uso:
  python scripts/sync_oficialteste.py --dry
  python scripts/sync_oficialteste.py
  python scripts/sync_oficialteste.py --verify-only
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import io
import json
import os
import re
import sys
import time
import urllib.request
import zipfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PM = ROOT / "wordpress-loja" / "pm-home"
SNIPPETS = ROOT / "wordpress-loja" / "snippets"
MANIFEST = SNIPPETS / "manifest.json"
DEFAULT_ENV = ROOT / "projeto-migracao" / ".secrets" / "oficialteste.env"

PROD = "https://loja.pellomenos.com.br"
PROD_UPLOADS = PROD + "/wp-content/uploads/pm-home/"
SKIP_DIRS = {"media", "fonts"}
BATCH_BYTES = 4 * 1024 * 1024
UA = {"User-Agent": "pm-sync-oficialteste"}
FORCE_RETRY = 3
# O CDN do destino pode servir o arquivo anterior por alguns segundos
VERIFY_RETRY = 3
VERIFY_RETRY_DELAY = 8


# ---------------------------------------------------------------- credenciais
def read_env_file(path: Path) -> dict:
    e = {}
    if not path.is_file():
        return e
    for line in path.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            e[k.strip().lstrip("﻿")] = v.strip()
    return e


def target() -> tuple[str, dict]:
    url = os.environ.get("PM_SYNC_URL")
    user = os.environ.get("PM_SYNC_USER")
    pwd = os.environ.get("PM_SYNC_APP_PASSWORD")
    if url and user and pwd:
        base = url
        cred = (user, pwd)
    else:
        e = read_env_file(DEFAULT_ENV)
        base = e.get("PM_OFICIALTESTE_URL", "")
        cred = (e.get("PM_OFICIALTESTE_USER", ""), e.get("PM_OFICIALTESTE_APP_PASSWORD", ""))
    if not base or not cred[0] or not cred[1]:
        raise SystemExit("sem credenciais: defina PM_SYNC_URL / PM_SYNC_USER / PM_SYNC_APP_PASSWORD")
    if "loja.pellomenos.com.br" in base:
        raise SystemExit("ABORTADO: destino aponta para a loja de producao")
    tok = base64.b64encode(f"{cred[0]}:{cred[1]}".encode()).decode()
    return base.rstrip("/"), {"Authorization": "Basic " + tok, **UA}


# ---------------------------------------------------------------- manifesto
def manifest_paths() -> list[str]:
    """Caminhos relativos a uploads/pm-home, derivados do repositorio."""
    out = []
    for p in PM.rglob("*"):
        if not p.is_file():
            continue
        if set(p.relative_to(PM).parts) & SKIP_DIRS:
            continue
        if ".bak" in p.name or p.name.endswith(".pre-regulariza.json"):
            continue
        out.append(str(p.relative_to(PM)).replace("\\", "/"))
    return sorted(out)


# ---------------------------------------------------------------- http
def fetch(url: str, timeout: int = 90, tentativas: int = FORCE_RETRY) -> bytes | None:
    for i in range(tentativas):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
                return r.read()
        except Exception:
            if i == tentativas - 1:
                return None
    return None


def api(base: str, h: dict, method: str, path: str, payload=None):
    data = None if payload is None else json.dumps(payload).encode()
    hh = dict(h)
    if payload is not None:
        hh["Content-Type"] = "application/json"
    req = urllib.request.Request(base + path, data=data, method=method, headers=hh)
    with urllib.request.urlopen(req, timeout=180) as r:
        body = r.read().decode("utf-8", "replace")
        return r.status, (json.loads(body) if body.strip()[:1] in "{[" else body)


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


# ---------------------------------------------------------------- etapas
def download_from_prod(paths: list[str]) -> dict[str, bytes]:
    print(f"== 1. baixando da loja ({len(paths)} arquivos) ==")

    def baixa(rel: str):
        return rel, fetch(PROD_UPLOADS + rel)

    with ThreadPoolExecutor(max_workers=8) as ex:
        pares = list(ex.map(baixa, paths))

    dados, faltando = {}, []
    for rel, b in pares:
        if b is None:
            faltando.append(rel)
        else:
            dados[rel] = b
    print(f"  baixados: {len(dados)} | ausentes na loja: {len(faltando)}")
    for f in faltando[:10]:
        print("    faltando:", f)
    return dados


def upload_to_test(base: str, h: dict, dados: dict[str, bytes], dry: bool) -> int:
    print(f"\n== 2. enviando ao teste ({len(dados)} arquivos) ==")
    lotes, atual, tamanho = [], {}, 0
    for rel, b in dados.items():
        if atual and tamanho + len(b) > BATCH_BYTES:
            lotes.append(atual)
            atual, tamanho = {}, 0
        atual[rel] = b
        tamanho += len(b)
    if atual:
        lotes.append(atual)

    if dry:
        for i, lote in enumerate(lotes, 1):
            print(f"  lote {i}: {len(lote)} arquivos, {sum(len(v) for v in lote.values())/1048576:.1f} MB")
        return 0

    enviados = 0
    for i, lote in enumerate(lotes, 1):
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
            for rel, b in lote.items():
                z.writestr(rel, b)
        req = urllib.request.Request(
            base + "/wp-json/pm-home/v1/bundle",
            data=buf.getvalue(), method="POST",
            headers={**h, "Content-Type": "application/zip", "Accept": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=900) as r:
            resp = r.read()
        print(f"  lote {i}/{len(lotes)}: {len(lote)} arquivos, {len(buf.getvalue())//1024} KB -> {r.status} {resp[:40]}")
        enviados += len(lote)
    return enviados


def sync_snippets(base: str, h: dict, shell_ver: str, dry: bool) -> list[str]:
    print("\n== 3. snippets ==")
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))["snippets"]
    rows = json.load(urllib.request.urlopen(
        urllib.request.Request(base + "/wp-json/code-snippets/v1/snippets?per_page=100", headers=h), timeout=90))
    by_name = {s.get("name"): s for s in rows}
    problemas = []

    for item in manifest:
        nome = item["name"]
        alvo = by_name.get(nome)
        if not alvo:
            problemas.append(f"snippet ausente no destino: {nome}")
            print(f"  {nome:40s} AUSENTE")
            continue
        codigo = (SNIPPETS / item["file"]).read_text(encoding="utf-8")
        if "checkout-shell-c24.js" in codigo and shell_ver:
            codigo = re.sub(r"checkout-shell-c24\.js\?v=[A-Za-z0-9._-]+",
                            f"checkout-shell-c24.js?v={shell_ver}", codigo)

        igual = codigo == (alvo.get("code") or "") and bool(alvo.get("active")) == bool(item["active"])
        print(f"  {nome:40s} id={alvo['id']:3d} ativo={str(item['active']):5s} {'ok' if igual else 'atualizar'}")
        if igual or dry:
            continue

        st, saved = api(base, h, "PUT", f"/wp-json/code-snippets/v1/snippets/{alvo['id']}",
                        {"name": nome, "code": codigo,
                         "scope": alvo.get("scope") or "global", "active": bool(item["active"])})
        if st != 200 or codigo != (saved.get("code") or ""):
            problemas.append(f"falha ao publicar {nome} (status {st})")
    return problemas


def verify(base: str, dados: dict[str, bytes]) -> list[dict]:
    print("\n== 4. verificacao teste x loja ==")

    def checa(item):
        rel, esperado = item
        b = fetch(base + "/wp-content/uploads/pm-home/" + rel)
        if b is None:
            return {"arquivo": rel, "problema": "ausente no teste"}
        if sha(b) != sha(esperado):
            return {"arquivo": rel, "problema": "conteudo diferente"}
        return None

    with ThreadPoolExecutor(max_workers=8) as ex:
        res = list(ex.map(checa, dados.items()))
    falhas = [r for r in res if r]

    # CDN do destino pode servir a versao anterior por alguns segundos depois do
    # upload; reconfere so os divergentes antes de dar o sync como falho.
    for tentativa in range(1, VERIFY_RETRY + 1):
        if not falhas:
            break
        print(f"  reconferindo {len(falhas)} arquivo(s) — tentativa {tentativa}/{VERIFY_RETRY}")
        time.sleep(VERIFY_RETRY_DELAY * tentativa)
        por_nome = {r["arquivo"]: r for r in falhas}
        pendentes = [(rel, dados[rel]) for rel in por_nome if rel in dados]
        with ThreadPoolExecutor(max_workers=8) as ex:
            novas = [r for r in ex.map(checa, pendentes) if r]
        falhas = novas
    return falhas


def public_shell_version() -> str:
    html = fetch(PROD + "/finalizar-pagamento/")
    if not html:
        return ""
    m = re.search(r"checkout-shell-c24\.js\?v=([A-Za-z0-9._-]+)", html.decode("utf-8", "replace"))
    return m.group(1) if m else ""


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--verify-only", action="store_true")
    args = ap.parse_args()

    base, h = target()
    paths = manifest_paths()
    shell = public_shell_version()
    print(f"destino : {base}")
    print(f"origem  : {PROD}")
    print(f"shell   : {shell or '(nao detectado)'}")
    print(f"manifesto: {len(paths)} arquivos\n")

    dados = download_from_prod(paths)

    if args.verify_only:
        falhas = verify(base, dados)
        print(f"divergentes: {len(falhas)}")
        for f in falhas[:20]:
            print("  ", f)
        sys.exit(1 if falhas else 0)

    upload_to_test(base, h, dados, args.dry)
    problemas = sync_snippets(base, h, shell, args.dry)

    if args.dry:
        print("\n(dry-run) nada foi publicado")
        return

    falhas = verify(base, dados)
    print(f"divergentes: {len(falhas)}")
    for f in falhas[:20]:
        print("  ", f)

    print("\n== resumo ==")
    print(f"  arquivos espelhados : {len(dados)}")
    print(f"  snippets com falha  : {len(problemas)}")
    print(f"  arquivos divergentes: {len(falhas)}")
    if problemas or falhas:
        for p in problemas:
            print("  snippet:", p)
        sys.exit(1)
    print("  OK: teste identico a producao")


if __name__ == "__main__":
    main()