# -*- coding: utf-8 -*-
"""Sobe a imagem de cada produto novo para a biblioteca de midia e define como
imagem do produto no WooCommerce. Nao altera preco nem visibilidade.

Uso: python scripts/_upload_product_images.py [--write] [--limit N]
"""
from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PM = ROOT / "wordpress-loja" / "pm-home"
CR = PM / "cart-related.json"
OLD = PM / "cart-related.pre-regulariza.json"
REPORT = ROOT / "scripts" / "_images_report.json"


def env() -> dict:
    e = {}
    for line in (ROOT / "projeto-migracao" / ".secrets" / "loja.env").read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            e[k.strip().lstrip("﻿")] = v.strip()
    return e


class Api:
    def __init__(self) -> None:
        e = env()
        self.base = e["PM_LOJA_URL"].rstrip("/")
        tok = base64.b64encode(
            f"{e['PM_LOJA_USER']}:{e['PM_LOJA_APP_PASSWORD']}".encode()
        ).decode()
        self.auth = "Basic " + tok

    def media(self, path: Path, title: str, alt: str):
        ctype = mimetypes.guess_type(path.name)[0] or "image/webp"
        req = urllib.request.Request(
            self.base + "/wp-json/wp/v2/media",
            data=path.read_bytes(),
            method="POST",
            headers={
                "Authorization": self.auth,
                "User-Agent": "pm-images",
                "Content-Type": ctype,
                "Content-Disposition": f'attachment; filename="{path.name}"',
                "Accept": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                body = json.load(r)
            mid = body.get("id")
            if mid:
                # alt text + titulo para acessibilidade/SEO
                upd = urllib.request.Request(
                    self.base + f"/wp-json/wp/v2/media/{mid}",
                    data=json.dumps({"alt_text": alt, "title": title}).encode(),
                    method="POST",
                    headers={
                        "Authorization": self.auth,
                        "User-Agent": "pm-images",
                        "Content-Type": "application/json",
                    },
                )
                with urllib.request.urlopen(upd, timeout=120) as r2:
                    r2.read()
            return 201, body
        except urllib.error.HTTPError as err:
            return err.code, err.read().decode("utf-8", "replace")[:300]

    def set_image(self, pid: str, media_id: int):
        req = urllib.request.Request(
            self.base + f"/wp-json/wc/v3/products/{pid}",
            data=json.dumps({"images": [{"id": media_id}]}).encode(),
            method="PUT",
            headers={
                "Authorization": self.auth,
                "User-Agent": "pm-images",
                "Content-Type": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                body = json.load(r)
            return 200, body.get("images")
        except urllib.error.HTTPError as err:
            return err.code, err.read().decode("utf-8", "replace")[:300]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    cr = json.loads(CR.read_text(encoding="utf-8"))["products"]
    old = json.loads(OLD.read_text(encoding="utf-8"))["products"]
    novos = [
        k for k in cr
        if cr[k].get("units")
        and str(cr[k].get("productId")) != str(old.get(k, {}).get("productId"))
    ]
    print("produtos novos:", len(novos))

    plano = []
    for k in sorted(novos):
        row = cr[k]
        img = (row.get("image") or "").split("?")[0]
        p = ROOT / "public" / img.lstrip("/")
        plano.append({"key": k, "pid": str(row["productId"]), "name": row.get("name"),
                      "image": img, "exists": p.is_file(), "path": str(p)})

    faltando = [x for x in plano if not x["exists"]]
    print("sem arquivo local:", len(faltando), [x["key"] for x in faltando][:10])
    print()
    for x in plano[:5]:
        print(f"  {x['key']:28s} pid={x['pid']:6s} -> {x['image']}")

    REPORT.write_text(json.dumps(plano, ensure_ascii=False, indent=2), encoding="utf-8")

    if not args.write:
        print("\n(dry-run; use --write)")
        return

    api = Api()
    ok = fail = 0
    resultados = []
    for i, x in enumerate(plano, 1):
        if args.limit and i > args.limit:
            break
        if not x["exists"]:
            resultados.append({**x, "status": "SEM_ARQUIVO"})
            fail += 1
            continue
        path = Path(x["path"])
        st, body = api.media(path, x["name"] or x["key"], x["name"] or x["key"])
        if st not in (200, 201) or not isinstance(body, dict) or not body.get("id"):
            print(f"  ERRO midia {x['key']}: {st} {str(body)[:140]}")
            resultados.append({**x, "status": "ERRO_MIDIA", "detail": str(body)[:200]})
            fail += 1
            continue
        mid = body["id"]
        st2, imgs = api.set_image(x["pid"], mid)
        if st2 != 200:
            print(f"  ERRO produto {x['key']} ({x['pid']}): {st2} {str(imgs)[:140]}")
            resultados.append({**x, "status": "ERRO_PRODUTO", "media": mid, "detail": str(imgs)[:200]})
            fail += 1
            continue
        ok += 1
        resultados.append({**x, "status": "OK", "media": mid})
        if i % 10 == 0:
            print(f"  ... {i}/{len(plano)} (ok={ok} fail={fail})")
        time.sleep(0.1)

    REPORT.write_text(json.dumps(resultados, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nOK: {ok} | falhas: {fail} | relatorio: {REPORT}")


if __name__ == "__main__":
    main()