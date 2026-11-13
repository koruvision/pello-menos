# -*- coding: utf-8 -*-
"""Linha em todas as unidades (exceto SGO removida) + strip sgo do bridge.

READ/WRITE: oficialteste Woo via App Password + woo-bridge.json local.
"""
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

# Labels Woo for units that may need create/fix
OPTION_LABEL = {
    "ape": "RJ - Tijuca - Afonso Pena",
    "13m": "RJ - Centro - Rua Treze de Maio",
    "sp-aug": "SP - Capital - Rua Augusta",
}

SLUG_MAP = {
    "saogoncalo": None,  # dropped
    "saojoaodemeriti": None,  # SJM removida do ecommerce
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
            "User-Agent": "pm-linha-all-drop-sgo",
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
            return e.code, body[:500]


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
    if "sao goncalo" in n or "partage" in n:
        return None  # drop
    if raw in OPTION_LABEL.values():
        return {v: k for k, v in OPTION_LABEL.items()}[raw]
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
        ("barata ribeiro", "ton"),
        ("ipanema", "ipa"),
        ("otavio tarquino", "nig"),
        ("recreio", "rec"),
        ("goncalves dias", "cen"),
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


def strip_sgo_everywhere(bridge: dict) -> int:
    n = 0
    for pid, row in bridge.items():
        if not isinstance(row, dict):
            continue
        units = row.get("units")
        if isinstance(units, dict) and "sgo" in units:
            del units["sgo"]
            n += 1
    return n


def catalog_unit_ids() -> set[str]:
    return {
        c.lower().replace(" ", "-")
        for c in re.findall(r'unit\(\s*"([^"]+)"', DATA.read_text(encoding="utf-8"))
    }


def ensure_linha(base: str, auth: str, bridge: dict, all_ids: set[str]):
    for pid in LINHA:
        row = bridge[pid]
        wid = row["productId"]
        st, product = api("GET", f"{base}/wp-json/wc/v3/products/{wid}", auth)
        assert st == 200, (pid, st, product)
        attr_name = "Unidade"
        for a in product.get("attributes") or []:
            if a.get("variation"):
                attr_name = a.get("name") or attr_name

        # ensure parent attribute options include needed labels
        attrs = product.get("attributes") or []
        for a in attrs:
            if a.get("name") == attr_name:
                opts = list(a.get("options") or [])
                # drop sao goncalo labels
                opts = [o for o in opts if "goncalo" not in norm(o) and "gonçalo" not in (o or "").lower()]
                for label in OPTION_LABEL.values():
                    if label not in opts:
                        opts.append(label)
                a["options"] = opts
                a["visible"] = True
                a["variation"] = True
        api("PUT", f"{base}/wp-json/wc/v3/products/{wid}", auth, {"attributes": attrs})

        st, vars_ = api(
            "GET", f"{base}/wp-json/wc/v3/products/{wid}/variations?per_page=100", auth
        )
        assert st == 200

        # map current
        mapped = {}
        empty_ids = []
        sgo_var_ids = []
        for v in vars_:
            option = ""
            for a in v.get("attributes") or []:
                option = a.get("option") or option
            if not option:
                empty_ids.append(v["id"])
                continue
            if "goncalo" in norm(option) or option.strip() in ("saogoncalo",):
                sgo_var_ids.append(v["id"])
                # private / out of stock rather than delete (safer)
                api(
                    "PUT",
                    f"{base}/wp-json/wc/v3/products/{wid}/variations/{v['id']}",
                    auth,
                    {"status": "private", "stock_status": "outofstock"},
                )
                print(pid, "hide sgo var", v["id"], option)
                continue
            uid = map_opt(option)
            if uid and uid in all_ids:
                mapped[uid] = {"variationId": int(v["id"]), "option": option}

        missing = sorted(all_ids - set(mapped.keys()))
        print(pid, "mapped", len(mapped), "/", len(all_ids), "missing", missing, "empty", empty_ids)

        # assign empty vars or create for missing labels we know
        for uid in list(missing):
            label = OPTION_LABEL.get(uid)
            if not label:
                # try find leftover unmapped var by creating with a reasonable label from store name — skip unknown
                print(pid, "NO_LABEL_FOR", uid)
                continue
            if empty_ids:
                vid = empty_ids.pop(0)
                st, upd = api(
                    "PUT",
                    f"{base}/wp-json/wc/v3/products/{wid}/variations/{vid}",
                    auth,
                    {
                        "attributes": [{"name": attr_name, "option": label}],
                        "status": "publish",
                        "stock_status": "instock",
                        "regular_price": "1.00",
                    },
                )
                print(pid, "fix empty", vid, "->", uid, label, st)
                if st in (200, 201):
                    mapped[uid] = {"variationId": int(vid), "option": label}
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
                print(
                    pid,
                    "create",
                    uid,
                    label,
                    st,
                    created.get("id") if isinstance(created, dict) else created,
                )
                if st in (200, 201) and isinstance(created, dict) and created.get("id"):
                    mapped[uid] = {"variationId": int(created["id"]), "option": label}

        # re-fetch to confirm attribute stuck
        st, vars_ = api(
            "GET", f"{base}/wp-json/wc/v3/products/{wid}/variations?per_page=100", auth
        )
        mapped2 = {}
        for v in vars_:
            if v.get("status") == "private":
                continue
            option = ""
            for a in v.get("attributes") or []:
                option = a.get("option") or option
            if not option:
                continue
            uid = map_opt(option)
            if uid and uid in all_ids:
                mapped2[uid] = {"variationId": int(v["id"]), "option": option}
        missing2 = sorted(all_ids - set(mapped2.keys()))
        print(pid, "FINAL", len(mapped2), "/", len(all_ids), "missing", missing2)
        row["units"] = mapped2


def scrub_cf7_unit_select(base: str, auth: str):
    st, form = api("GET", f"{base}/wp-json/contact-form-7/v1/contact-forms/1831", auth)
    if st != 200 or not isinstance(form, dict):
        print("cf7 get", st)
        return
    props = form.get("properties") or {}
    form_prop = props.get("form") or {}
    content = form_prop.get("content") if isinstance(form_prop, dict) else form_prop
    if not isinstance(content, str):
        print("cf7 no content")
        return
    # remove quoted options containing goncalo / partage sao goncalo
    new = re.sub(
        r'\s*"[^"]*(?:Gonçalo|Goncalo|goncalo|saogoncalo)[^"]*"',
        "",
        content,
        flags=re.I,
    )
    if new == content:
        print("cf7: no Sao Goncalo option found in form content")
        return
    # PUT via CF7 REST — properties.form may need full properties
    payload = {
        "properties": {
            **props,
            "form": {**form_prop, "content": new} if isinstance(form_prop, dict) else new,
        }
    }
    st2, upd = api(
        "POST",
        f"{base}/wp-json/contact-form-7/v1/contact-forms/1831",
        auth,
        payload,
    )
    # CF7 often uses POST for update
    print("cf7 update", st2, "removed goncalo options")


def main():
    e = env()
    base = e["PM_OFICIALTESTE_URL"].rstrip("/")
    auth = base64.b64encode(
        f"{e['PM_OFICIALTESTE_USER']}:{e['PM_OFICIALTESTE_APP_PASSWORD']}".encode()
    ).decode()
    all_ids = catalog_unit_ids()
    assert "sgo" not in all_ids, "SGO still in data.ts"
    print("catalog units", len(all_ids), sorted(all_ids))

    bridge = json.loads(BRIDGE.read_text(encoding="utf-8"))
    n = strip_sgo_everywhere(bridge)
    print("stripped sgo from", n, "products in bridge")

    ensure_linha(base, auth, bridge, all_ids)
    scrub_cf7_unit_select(base, auth)

    BRIDGE.write_text(json.dumps(bridge, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    shutil.copy2(BRIDGE, BRIDGE_WP)
    print("saved bridges")


if __name__ == "__main__":
    main()
