# -*- coding: utf-8 -*-
import base64
import json
import re
import shutil
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


def env():
    d = {}
    for line in ENV.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            d[k.strip()] = v.strip()
    return d


def get(url, auth):
    req = urllib.request.Request(
        url, headers={"Authorization": "Basic " + auth, "User-Agent": "pm", "Accept": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=90) as r:
        return json.loads(r.read().decode())


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
    n = norm(option)
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
        ("nova iguacu i ", "nig"),
        ("recreio", "rec"),
        ("goncalves dias", "cen"),
        ("sao goncalo", "sgo"),
        ("partage", "sgo"),
        ("nilopolis", "nil"),
        ("largo do machado", "lma"),
        ("petropolis", "pet"),
        ("galeao", "ig02"),
        ("ilha", "ig02"),
        ("humaita", "hut"),
        ("bangu", "ban"),
        ("botafogo", "bot"),
        ("copacabana ii", "copa-2"),
        ("nossa senhora de copacabana", "copa-2"),
        ("crystal", "eba"),
        ("bandeirantes", "eba"),
        ("flamengo", "fla"),
        ("freguesia", "fre"),
        ("icarai", "ica"),
        ("bicao", "lbi"),
        ("top shopping", "nig2"),
        ("nova iguacu ii", "nig2"),
        ("ao lado do top", "nig2"),
        ("ao lado top", "nig2"),
    ]
    for needle, uid in rules:
        if needle in n:
            return uid
    # bare "Nova Iguaçu" without I/II -> nig if not nig2 already
    if "nova iguacu" in n and "ii" not in n and "2" not in n and "top" not in n:
        return "nig"
    return None


def main():
    e = env()
    base = e["PM_OFICIALTESTE_URL"].rstrip("/")
    auth = base64.b64encode(f"{e['PM_OFICIALTESTE_USER']}:{e['PM_OFICIALTESTE_APP_PASSWORD']}".encode()).decode()
    all_ids = {c.lower().replace(" ", "-") for c in re.findall(r'unit\(\s*"([^"]+)"', DATA.read_text(encoding="utf-8"))}
    bridge = json.loads(BRIDGE.read_text(encoding="utf-8"))

    for pid in LINHA:
        row = bridge[pid]
        wid = row["productId"]
        vars_ = get(f"{base}/wp-json/wc/v3/products/{wid}/variations?per_page=100", auth)
        mapped = {}
        unmapped = []
        for v in vars_:
            option = ""
            for a in v.get("attributes") or []:
                option = a.get("option") or option
            uid = map_opt(option)
            if uid:
                mapped[uid] = {"variationId": int(v["id"]), "option": option}
            else:
                unmapped.append(option)
        # force ape/13m labels if present by id from OPTION text
        for v in vars_:
            option = ""
            for a in v.get("attributes") or []:
                option = a.get("option") or option
            if option == OPTION["ape"]:
                mapped["ape"] = {"variationId": int(v["id"]), "option": option}
            if option == OPTION["13m"]:
                mapped["13m"] = {"variationId": int(v["id"]), "option": option}

        missing = sorted(all_ids - set(mapped.keys()))
        print(pid, "mapped", len(mapped), "missing", missing)
        if unmapped:
            print("  unmapped options:", unmapped)
        row["units"] = mapped

    BRIDGE.write_text(json.dumps(bridge, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    shutil.copy2(BRIDGE, BRIDGE_WP)
    print("saved")


if __name__ == "__main__":
    main()
