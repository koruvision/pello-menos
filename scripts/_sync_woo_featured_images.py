# -*- coding: utf-8 -*-
"""Troca a imagem destacada dos produtos do WooCommerce pela foto oficial do catálogo.

Vários serviços do catálogo compartilham o mesmo produto Woo (ponte em src/lib/woo-bridge.json),
então cada produto Woo recebe a imagem do serviço "principal" do grupo (feminino, não esfoliação).
A imagem é convertida de .webp para .jpg (fundo branco) para funcionar em qualquer tela do Woo
(admin, e-mails, pedidos) e enviada à biblioteca de mídia com o nome `pm-<id>.jpg`; reexecutar
não duplica (reaproveita a mídia já enviada e pula produtos já corretos).

Uso:
    python scripts/_sync_woo_featured_images.py --env projeto-migracao/.secrets/oficialteste.env [--only 9276] [--dry-run]

Nunca roda contra loja.pellomenos.com.br sem --allow-prod.
"""
from __future__ import annotations

import argparse
import base64
import io
import json
import sys
import time
import urllib.error
import urllib.request
from collections import OrderedDict
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
BRIDGE = ROOT / "src" / "lib" / "woo-bridge.json"
RELATED = ROOT / "wordpress-loja" / "pm-home" / "cart-related.json"
PUBLIC = ROOT / "public"


def load_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        values[k.strip()] = v.strip()
    return values


def _cred(cfg: dict[str, str], suffix: str) -> str:
    for prefix in ("PM_LOJA", "PM_OFICIALTESTE", "PM_CLONE"):
        key = f"{prefix}_{suffix}"
        if key in cfg and cfg[key]:
            return cfg[key]
    raise KeyError(suffix)


class Api:
    def __init__(self, cfg: dict[str, str]):
        self.base = _cred(cfg, "URL").rstrip("/")
        token = base64.b64encode(
            f"{_cred(cfg, 'USER')}:{_cred(cfg, 'APP_PASSWORD')}".encode()
        ).decode()
        self.headers = {
            "Authorization": "Basic " + token,
            "Accept": "application/json",
            "User-Agent": "pm-woo-images/1.0",
        }

    def call(self, method: str, path: str, payload=None, raw: bytes | None = None, extra=None):
        headers = dict(self.headers)
        if extra:
            headers.update(extra)
        data = raw
        if payload is not None:
            data = json.dumps(payload).encode()
            headers["Content-Type"] = "application/json"
        req = urllib.request.Request(self.base + path, data=data, method=method, headers=headers)
        for attempt in range(3):
            try:
                with urllib.request.urlopen(req, timeout=180) as r:
                    body = r.read().decode("utf-8", "replace")
                    return r.status, (json.loads(body) if body.strip()[:1] in "{[" else body)
            except urllib.error.HTTPError as e:
                body = e.read().decode("utf-8", "replace")
                try:
                    return e.code, json.loads(body)
                except Exception:
                    return e.code, body[:600]
            except (urllib.error.URLError, TimeoutError) as e:
                if attempt == 2:
                    raise
                time.sleep(3)
        raise RuntimeError("unreachable")

    def get(self, path: str):
        st, body = self.call("GET", path)
        if st == 404:
            return None
        if st != 200:
            raise SystemExit(f"GET {path} -> {st} {body}")
        return body


def main_image_for_group(ids: list[str]) -> str:
    """Serviço principal do grupo: feminino e não-esfoliação; senão o primeiro."""
    for cid in ids:
        if not cid.endswith("-masc") and not cid.startswith("esfoliacao-"):
            return cid
    for cid in ids:
        if not cid.endswith("-masc"):
            return cid
    return ids[0]


def to_jpeg(path: Path) -> bytes:
    img = Image.open(path).convert("RGBA")
    bg = Image.new("RGB", img.size, (255, 255, 255))
    bg.paste(img, mask=img.split()[3])
    out = io.BytesIO()
    bg.save(out, "JPEG", quality=88, optimize=True, progressive=True)
    return out.getvalue()


def find_media(api: Api, filename_stem: str) -> dict | None:
    rows = api.get(f"/wp-json/wp/v2/media?search={filename_stem}&per_page=20")
    for row in rows:
        src = row.get("source_url", "")
        if f"/{filename_stem}." in src or f"/{filename_stem}-" in src:
            return row
    return None


def upload(api: Api, filename: str, blob: bytes, title: str, alt: str) -> dict:
    st, media = api.call(
        "POST",
        "/wp-json/wp/v2/media",
        raw=blob,
        extra={
            "Content-Type": "image/jpeg",
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )
    if st not in (200, 201) or not isinstance(media, dict):
        raise SystemExit(f"upload {filename} -> {st} {media}")
    api.call("POST", f"/wp-json/wp/v2/media/{media['id']}", {"title": title, "alt_text": alt})
    return media


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--env", required=True)
    ap.add_argument("--only", nargs="*", type=int, default=None, help="ids de produto Woo")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--allow-prod", action="store_true")
    args = ap.parse_args()

    cfg = load_env(ROOT / args.env)
    url = _cred(cfg, "URL")
    if "loja.pellomenos.com.br" in url and not args.allow_prod:
        raise SystemExit("recusado: destino é a loja de produção (use --allow-prod)")
    api = Api(cfg)

    bridge = json.loads(BRIDGE.read_text(encoding="utf-8"))
    related = json.loads(RELATED.read_text(encoding="utf-8"))["products"]

    groups: "OrderedDict[int, list[str]]" = OrderedDict()
    for cid, row in bridge.items():
        pid = row.get("productId")
        if not pid or cid == "produto-1-real":
            continue
        groups.setdefault(int(pid), []).append(cid)

    done = skipped = 0
    for pid, cids in groups.items():
        if args.only and pid not in args.only:
            continue
        cid = main_image_for_group(cids)
        info = related.get(cid)
        if not info:
            print(f"- {pid} {cid}: sem entrada no cart-related.json, pulando")
            skipped += 1
            continue
        image_rel = info["image"].split("?")[0].lstrip("/")
        local = PUBLIC / image_rel
        if not local.is_file():
            print(f"- {pid} {cid}: imagem local ausente {image_rel}, pulando")
            skipped += 1
            continue
        stem = f"pm-{cid}"
        product = api.get(f"/wp-json/wc/v3/products/{pid}")
        if product is None:
            print(f"- {pid} {cid}: produto ausente na loja, pulando")
            skipped += 1
            continue
        current = product.get("images") or []
        if current and f"/{stem}." in current[0].get("src", "") and len(current) == 1:
            print(f"= {pid} {product['name']}: já usa {stem}")
            skipped += 1
            continue
        print(f"> {pid} {product['name']} <- {cid} ({image_rel})", end=" ")
        if args.dry_run:
            print("[dry-run]")
            continue
        media = find_media(api, stem)
        if media is None:
            media = upload(api, f"{stem}.jpg", to_jpeg(local), product["name"], product["name"])
            print(f"upload #{media['id']}", end=" ")
        else:
            print(f"mídia #{media['id']} reaproveitada", end=" ")
        st, saved = api.call("PUT", f"/wp-json/wc/v3/products/{pid}", {"images": [{"id": media["id"]}]})
        if st != 200:
            raise SystemExit(f"PUT product {pid} -> {st} {saved}")
        # Variações com imagem própria (diferente da herdada) passam a usar a mesma imagem.
        fixed_vars = 0
        if product.get("type") == "variable":
            page = 1
            while True:
                vs = api.get(f"/wp-json/wc/v3/products/{pid}/variations?per_page=100&page={page}")
                if not vs:
                    break
                for v in vs:
                    img = v.get("image") or {}
                    if img.get("id") and int(img["id"]) != int(media["id"]):
                        st2, _ = api.call(
                            "PUT", f"/wp-json/wc/v3/products/{pid}/variations/{v['id']}", {"image": {"id": media["id"]}}
                        )
                        if st2 == 200:
                            fixed_vars += 1
                if len(vs) < 100:
                    break
                page += 1
        print(f"ok (variações ajustadas: {fixed_vars})")
        done += 1
    print(f"\nconcluído: {done} produtos atualizados, {skipped} pulados")


if __name__ == "__main__":
    sys.exit(main())
