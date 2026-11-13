# -*- coding: utf-8 -*-
"""Fix broken APE/13M variations + rebuild linha unit maps for all 37 stores."""
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

LINHA = ["buco-linha", "queixo-linha", "faixa-linha"]
OPTION = {
    "ape": "RJ - Tijuca - Afonso Pena",
    "13m": "RJ - Centro - Rua Treze de Maio",
}
# known slug-like options in Woo
SLUG_MAP = {
    "saogoncalo": "sgo",
    "saojoaodemeriti": "sjm",
}


def env():
    d = {}
    for line in ENV.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            d[k.strip()] = v.strip()
    return d


def api(method, url, auth, payload=None):
    data = None if payload is None else json.dumps(payload).encode()
    req = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={
            "Authorization": "Basic " + auth,
            "User-Agent": "pm-linha-finish",
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            body = r.read().decode("utf-8", "replace")
            return r.status, json.loads(body) if body[:1] in "[{" else body
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")
        try:
            return e.code, json.loads(body)
        except Exception:
            return e.code, body[:400]


def norm(s):
    s = (s or "").lower()
    for a, b in {
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
    }.items():
        s = s.replace(a, b)
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def map_opt(option: str):
    raw = (option or "").strip()
    if raw in SLUG_MAP:
        return SLUG_MAP[raw]
    n = norm(raw)
    if raw in OPTION.values():
        return {v: k for k, v in OPTION.items()}[raw]
    if "sao jose dos campos" in n:
        return "sp-sjc"
    if "rua sao jose" in n or ("centro" in n and "sao jose" in n and "campos" not in n):
        return "sjo"
    rules = [
        ("afonso pena", "ape"),
        ("treze de maio", "13m"),
        ("saens pena", "snp"),
        ("uruguai", "urg"),
        ("augusta", "sp-aug"),
        ("paulista", "sp-avp"),
        ("asa sul", "df-asu"),
        ("asa norte", "df-ano"),
        ("bonsucesso", "bon"),
        ("caxias", "cax"),
        ("campo grande", "cgr2"),
        ("leblon", "leb2"),
        ("madureira", "mad"),
        ("meier", "mei"),
        ("meriti", "sjm"),
        ("barata ribeiro", "ton"),
        ("ipanema", "ipa"),
        ("otavio tarquino", "nig"),
        ("recreio", "rec"),
        ("goncalves dias", "cen"),
        ("sao goncalo", "sgo"),
        ("nilopolis", "nil"),
        ("largo do machado", "lma"),
        ("petropolis", "pet"),
        ("galeao", "ig02"),
        ("ilha do governador", "ig02"),
        ("humaita", "hut"),
        ("bangu", "ban"),
        ("botafogo", "bot"),
        ("copacabana ii", "copa-2"),
        ("n s de copacabana", "copa-2"),
        ("nossa senhora de copacabana", "copa-2"),
        ("av n s copacabana", "copa-2"),
        ("crystal", "eba"),
        ("bandeirantes", "eba"),
        ("flamengo", "fla"),
        ("freguesia", "fre"),
        ("icarai", "ica"),
        ("bicao", "lbi"),
        ("top shopping", "nig2"),
        ("nova iguacu ii", "nig2"),
        ("nova iguacu i", "nig"),
    ]
    for needle, uid in rules:
        if needle in n:
            return uid
    if "nova iguacu" in n and "ii" not in n and "top" not in n:
        return "nig"
    return None


def main():
    e = env()
    base = e["PM_OFICIALTESTE_URL"].rstrip("/")
    auth = base64.b64encode(f"{e['PM_OFICIALTESTE_USER']}:{e['PM_OFICIALTESTE_APP_PASSWORD']}".encode()).decode()
    all_ids = {
        c.lower().replace(" ", "-")
        for c in re.findall(r'unit\(\s*"([^"]+)"', DATA.read_text(encoding="utf-8"))
    }
    bridge = json.loads(BRIDGE.read_text(encoding="utf-8"))

    for pid in LINHA:
        row = bridge[pid]
        wid = row["productId"]
        st, product = api("GET", f"{base}/wp-json/wc/v3/products/{wid}", auth)
        assert st == 200, (st, product)
        attr_name = "Unidade"
        for a in product.get("attributes") or []:
            if a.get("variation"):
                attr_name = a.get("name") or attr_name
        # ensure options include ape/13m labels
        attrs = product.get("attributes") or []
        for a in attrs:
            if a.get("name") == attr_name:
                opts = list(a.get("options") or [])
                for label in OPTION.values():
                    if label not in opts:
                        opts.append(label)
                a["options"] = opts
        api("PUT", f"{base}/wp-json/wc/v3/products/{wid}", auth, {"attributes": attrs})

        st, vars_ = api("GET", f"{base}/wp-json/wc/v3/products/{wid}/variations?per_page=100", auth)
        assert st == 200

        # fix empty-attribute variations (our broken creates) or create missing
        empty_ids = [v["id"] for v in vars_ if not (v.get("attributes") or [])]
        have_labels = set()
        for v in vars_:
            for a in v.get("attributes") or []:
                if a.get("option") in OPTION.values():
                    have_labels.add(a.get("option"))

        # assign empty vars to missing labels, or PUT recreate
        labels_needed = [OPTION[k] for k in ("ape", "13m") if OPTION[k] not in have_labels]
        for i, label in enumerate(labels_needed):
            if i < len(empty_ids):
                vid = empty_ids[i]
                st, upd = api(
                    "PUT",
                    f"{base}/wp-json/wc/v3/products/{wid}/variations/{vid}",
                    auth,
                    {
                        "attributes": [{"name": attr_name, "option": label}],
                        "status": "publish",
                        "stock_status": "instock",
                    },
                )
                print(pid, "fix empty var", vid, "->", label, st)
            else:
                st, created = api(
                    "POST",
                    f"{base}/wp-json/wc/v3/products/{wid}/variations",
                    auth,
                    {
                        "regular_price": "1.00",
                        "status": "publish",
                        "stock_status": "instock",
                        "attributes": [{"name": attr_name, "option": label}],
                    },
                )
                print(pid, "create", label, st, created.get("id") if isinstance(created, dict) else created)

        st, vars_ = api("GET", f"{base}/wp-json/wc/v3/products/{wid}/variations?per_page=100", auth)
        mapped = {}
        unmapped = []
        for v in vars_:
            option = ""
            for a in v.get("attributes") or []:
                option = a.get("option") or option
            if not option:
                unmapped.append(f"id={v['id']} empty")
                continue
            uid = map_opt(option)
            if uid:
                mapped[uid] = {"variationId": int(v["id"]), "option": option}
            else:
                unmapped.append(option)

        missing = sorted(all_ids - set(mapped.keys()))
        print(pid, "mapped", len(mapped), "/", len(all_ids), "missing", missing)
        if unmapped:
            print("  leftover", unmapped)
        row["units"] = mapped

    BRIDGE.write_text(json.dumps(bridge, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    shutil.copy2(BRIDGE, BRIDGE_WP)
    print("saved bridges")


if __name__ == "__main__":
    main()
