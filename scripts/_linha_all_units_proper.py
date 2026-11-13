# -*- coding: utf-8 -*-
"""Rebuild linha bridge units from Woo; create APE/13M variations if missing; update ProductPageView filter."""
from __future__ import annotations

import base64
import json
import re
import shutil
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BRIDGE = ROOT / "src" / "lib" / "woo-bridge.json"
BRIDGE_WP = ROOT / "wordpress-loja" / "pm-home" / "woo-bridge.json"
ENV = ROOT / "projeto-migracao" / ".secrets" / "oficialteste.env"
DATA = ROOT / "src" / "lib" / "data.ts"
PAGE = ROOT / "src" / "components" / "ProductPageView.tsx"

LINHA_IDS = ["buco-linha", "queixo-linha", "faixa-linha"]

# Canonical option labels used elsewhere in bridge for these units
OPTION = {
    "ape": "RJ - Tijuca - Afonso Pena",
    "13m": "RJ - Centro - Rua Treze de Maio",
}


def read_env():
    values = {}
    for line in ENV.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        values[k.strip()] = v.strip()
    return values


def api(method: str, url: str, auth: str, payload=None):
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={
            "Authorization": "Basic " + auth,
            "User-Agent": "pm-linha-all/1.0",
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            body = r.read().decode("utf-8", "replace")
            return r.status, (json.loads(body) if body[:1] in "[{" else body)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")
        try:
            parsed = json.loads(body)
        except Exception:
            parsed = body[:500]
        return e.code, parsed


def norm(s: str) -> str:
    s = (s or "").lower()
    repl = {
        "á": "a",
        "à": "a",
        "â": "a",
        "ã": "a",
        "é": "e",
        "ê": "e",
        "í": "i",
        "ó": "o",
        "ô": "o",
        "õ": "o",
        "ú": "u",
        "ç": "c",
    }
    for a, b in repl.items():
        s = s.replace(a, b)
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def unit_from_option(option: str) -> str | None:
    n = norm(option)
    table = [
        ("afonso pena", "ape"),
        ("treze de maio", "13m"),
        ("13 de maio", "13m"),
        ("rua treze", "13m"),
        ("saens pena", "snp"),
        ("uruguai", "urg"),
        ("augusta", "sp-aug"),
        ("paulista", "sp-avp"),
        ("sao jose dos campos", "sp-sjc"),
        ("asa sul", "df-asu"),
        ("asa norte", "df-ano"),
        ("bonsucesso", "bon"),
        ("caxias", "cax"),
        ("campo grande", "cgr2"),
        ("leblon", "leb2"),
        ("madureira", "mad"),
        ("meier", "mei"),
        ("meriti", "sjm"),
        ("sao jose", "sjo"),  # Centro Sao Jose — careful vs SJC
        ("barata ribeiro", "ton"),
        ("copacabana i", "ton"),
        ("ipanema", "ipa"),
        ("otavio tarquino", "nig"),
        ("nova iguacu i", "nig"),
        ("recreio", "rec"),
        ("goncalves dias", "cen"),
        ("sao goncalo", "sgo"),
        ("partage", "sgo"),
        ("nilopolis", "nil"),
        ("largo do machado", "lma"),
        ("petropolis", "pet"),
        ("galeao", "ig02"),
        ("ilha do governador", "ig02"),
        ("humaita", "hut"),
        ("bangu", "ban"),
        ("botafogo", "bot"),
        ("nossa senhora de copacabana", "copa-2"),
        ("copacabana ii", "copa-2"),
        ("crystal mall", "eba"),
        ("estrada dos bandeirantes", "eba"),
        ("estrada bandeirantes", "eba"),
        ("flamengo", "fla"),
        ("freguesia", "fre"),
        ("icaraí", "ica"),
        ("icarai", "ica"),
        ("bicao", "lbi"),
        ("top shopping", "nig2"),
        ("nova iguacu ii", "nig2"),
    ]
    # Sao Jose Centro vs SJC
    if "sao jose dos campos" in n:
        return "sp-sjc"
    if "rua sao jose" in n or (n.startswith("rj centro") and "sao jose" in n):
        return "sjo"
    for needle, uid in table:
        if needle in n:
            return uid
    return None


def main():
    env = read_env()
    base = env["PM_OFICIALTESTE_URL"].rstrip("/")
    auth = base64.b64encode(
        f"{env['PM_OFICIALTESTE_USER']}:{env['PM_OFICIALTESTE_APP_PASSWORD']}".encode()
    ).decode()

    all_ids = {
        c.lower().replace(" ", "-") for c in re.findall(r'unit\(\s*"([^"]+)"', DATA.read_text(encoding="utf-8"))
    }
    bridge = json.loads(BRIDGE.read_text(encoding="utf-8"))

    for pid in LINHA_IDS:
        row = bridge[pid]
        pid_woo = row["productId"]
        status, product = api("GET", f"{base}/wp-json/wc/v3/products/{pid_woo}", auth)
        if status != 200:
            raise SystemExit(f"product {pid}: {status} {product}")
        status, variations = api(
            "GET", f"{base}/wp-json/wc/v3/products/{pid_woo}/variations?per_page=100", auth
        )
        if status != 200:
            raise SystemExit(f"variations {pid}: {status} {variations}")

        # attribute name for unidade
        attr_name = None
        for a in product.get("attributes") or []:
            if a.get("variation"):
                attr_name = a.get("name")
                break
        if not attr_name and variations:
            attrs = variations[0].get("attributes") or []
            if attrs:
                attr_name = attrs[0].get("name")
        print(pid, "attr", attr_name, "vars", len(variations))

        mapped = {}
        for v in variations:
            option = ""
            for a in v.get("attributes") or []:
                option = a.get("option") or option
            uid = unit_from_option(option)
            if uid:
                mapped[uid] = {"variationId": int(v["id"]), "option": option}

        # template variation for price/stock
        template = variations[0] if variations else None
        for need in ("ape", "13m"):
            if need in mapped:
                continue
            if not template or not attr_name:
                print("cannot create", need, "no template")
                continue
            # ensure option exists on product attribute
            attrs = product.get("attributes") or []
            for a in attrs:
                if a.get("name") == attr_name:
                    opts = list(a.get("options") or [])
                    if OPTION[need] not in opts:
                        opts.append(OPTION[need])
                        a["options"] = opts
            api(
                "PUT",
                f"{base}/wp-json/wc/v3/products/{pid_woo}",
                auth,
                {"attributes": attrs},
            )
            payload = {
                "regular_price": template.get("regular_price") or "0",
                "sale_price": template.get("sale_price") or "",
                "status": "publish",
                "manage_stock": False,
                "stock_status": "instock",
                "attributes": [{"name": attr_name, "option": OPTION[need]}],
            }
            st, created = api(
                "POST", f"{base}/wp-json/wc/v3/products/{pid_woo}/variations", auth, payload
            )
            print("create", need, st, created.get("id") if isinstance(created, dict) else created)
            if st in (200, 201) and isinstance(created, dict):
                mapped[need] = {
                    "variationId": int(created["id"]),
                    "option": OPTION[need],
                }

        missing = sorted(all_ids - set(mapped.keys()))
        print(pid, "mapped", len(mapped), "missing", missing)
        row["units"] = mapped

    BRIDGE.write_text(json.dumps(bridge, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    shutil.copy2(BRIDGE, BRIDGE_WP)

    # ProductPageView: for all-store methods, don't hide units missing from bridge
    text = PAGE.read_text(encoding="utf-8")
    old = """  const availableUnits = useMemo(() => {
    const capacity = unitsForProduct(product);
    const map = bridge?.units;
    if (!map || Object.keys(map).length === 0) return capacity;
    return capacity.filter((unit) => Boolean(map[unit.id]));
  }, [product, bridge]);"""
    new = """  const availableUnits = useMemo(() => {
    const capacity = unitsForProduct(product);
    const map = bridge?.units;
    // Linha / esfoliação / presente / body-splash: capacidade já é todas as lojas.
    // Não esconder unidade só porque a variação Woo ainda não está no bridge.
    const allStoresMethod =
      product.method === "linha" ||
      product.method === "esfoliacao" ||
      product.method === "presente" ||
      product.method === "produto" ||
      product.id === "body-splash" ||
      product.id === "body-splash-masc";
    if (allStoresMethod || !map || Object.keys(map).length === 0) return capacity;
    return capacity.filter((unit) => Boolean(map[unit.id]));
  }, [product, bridge]);"""
    if old not in text:
        if "allStoresMethod" in text:
            print("ProductPageView already patched")
        else:
            raise SystemExit("ProductPageView block not found")
    else:
        PAGE.write_text(text.replace(old, new), encoding="utf-8")
        print("patched ProductPageView")


if __name__ == "__main__":
    main()
