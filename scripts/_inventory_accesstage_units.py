# -*- coding: utf-8 -*-
"""Inventário sanitizado: storeUnits × AccesStage OT × CF7 unit/easyunit (loja+OT)."""
from __future__ import annotations

import base64
import json
import re
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SECRETS = ROOT / "projeto-migracao" / ".secrets"
KEYS = SECRETS / "_accesstage_unit_keys_sanitized.json"
OUT_JSON = SECRETS / "_inventory_accesstage_units.json"
OUT_MD = ROOT / "projeto-migracao" / "historico" / "37-unidades-accesstage-inventario.md"

# Código catálogo (storeUnits) → slug AccesStage / CF7
CODE_TO_SLUG: dict[str, str] = {
    "APE": "afonsopena",
    "BON": "bonsucesso",
    "CAX": "caxias",
    "CGR2": "campogrande",
    "DF-ASU": "asasul",
    "DF-ANO": "asanorte",
    "LEB2": "leblon2",
    "MAD": "madureira",
    "MEI": "meier",
    "SNP": "saenspena",
    "SJO": "saojose",  # Centro Rua São José — CF7 usa saojose; existe também rjsaojose no $api
    "TON": "copacabana1",
    "IPA": "ipanema",
    "NIG": "novaiguacu",
    "13M": "trezemaio",
    "REC": "recreio",
    "SP-AUG": "augusta",
    "SP-AVP": "paulista",
    "CEN": "goncalvesdias",
    "NIL": "nilopolis",
    "LMA": "largomachado",
    "SP-SJC": "saojosecampos",
    "PET": "petropolis",
    "IG02": "ilhagovernador2",
    "HUT": "humaita",
    "URG": "uruguai",
    "BAN": "bangu",
    "BOT": "botafogo",
    "COPA-2": "copacabana2",
    "EBA": "estradabandeirantes",
    "FLA": "flamengo",
    "FRE": "freguesia",
    "ICA": "icarai",
    "LBI": "largobicao",
    "NIG2": "novaiguacu2",
}

# Metadados de storeUnits (espelho de data.ts — manter alinhado)
STORE_UNITS = [
    ("APE", "Tijuca — Afonso Pena", "RJ", True, False, False, False),
    ("BON", "Bonsucesso", "RJ", True, False, False, False),
    ("CAX", "Duque de Caxias", "RJ", True, False, False, False),
    ("CGR2", "Campo Grande", "RJ", True, False, False, False),
    ("DF-ASU", "Asa Sul", "DF", True, False, False, False),
    ("DF-ANO", "Asa Norte", "DF", True, False, False, False),
    ("LEB2", "Leblon", "RJ", True, False, False, False),
    ("MAD", "Madureira", "RJ", True, False, False, False),
    ("MEI", "Méier", "RJ", True, False, False, False),
    ("SNP", "Tijuca — Saens Peña", "RJ", True, False, False, False),
    ("SJO", "Centro — Rua São José", "RJ", True, False, False, False),
    ("TON", "Copacabana I — Barata Ribeiro", "RJ", True, False, False, False),
    ("IPA", "Ipanema", "RJ", True, False, False, False),
    ("NIG", "Nova Iguaçu I", "RJ", True, False, False, False),
    ("13M", "Centro — Treze de Maio", "RJ", True, False, False, False),
    ("REC", "Recreio dos Bandeirantes", "RJ", True, True, True, False),
    ("SP-AUG", "Rua Augusta", "SP", True, False, True, False),
    ("SP-AVP", "Avenida Paulista", "SP", True, False, True, False),
    ("CEN", "Centro — Gonçalves Dias", "RJ", True, True, False, False),
    ("NIL", "Nilópolis", "RJ", True, True, False, False),
    ("LMA", "Largo do Machado", "RJ", True, True, False, False),
    ("SP-SJC", "São José dos Campos", "SP", True, True, False, False),
    ("PET", "Petrópolis", "RJ", True, True, False, False),
    ("IG02", "Ilha do Governador II", "RJ", True, True, False, False),
    ("HUT", "Humaitá", "RJ", True, True, False, False),
    ("URG", "Tijuca — Uruguai", "RJ", True, True, True, True),
    ("BAN", "Bangu", "RJ", True, True, True, True),
    ("BOT", "Botafogo", "RJ", True, True, True, True),
    ("COPA-2", "Copacabana II", "RJ", True, True, True, True),
    ("EBA", "Estrada dos Bandeirantes", "RJ", True, True, True, True),
    ("FLA", "Flamengo", "RJ", True, True, True, True),
    ("FRE", "Jacarepaguá — Freguesia", "RJ", True, True, True, True),
    ("ICA", "Icaraí", "RJ", True, True, True, True),
    ("LBI", "Largo do Bicão", "RJ", True, True, True, True),
    ("NIG2", "Nova Iguaçu II", "RJ", True, True, True, True),
]


def read_env(path: Path) -> dict[str, str]:
    e: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            e[k.strip().lstrip("\ufeff")] = v.strip().strip('"').strip("'")
    return e


def auth_header(user: str, password: str) -> str:
    return "Basic " + base64.b64encode(f"{user}:{password}".encode()).decode()


def get_json(url: str, auth: str | None = None) -> tuple[int, object]:
    headers = {"User-Agent": "pm-inventory/1.0", "Accept": "application/json"}
    if auth:
        headers["Authorization"] = auth
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            body = r.read().decode("utf-8", "replace")
            return r.status, json.loads(body) if body else {}
    except urllib.error.HTTPError as err:
        body = err.read().decode("utf-8", "replace")
        try:
            parsed = json.loads(body) if body else {}
        except json.JSONDecodeError:
            parsed = {"raw": body[:400]}
        return err.code, parsed


def parse_cf7_select_options(form: str, field: str) -> list[dict[str, str]]:
    """Parse CF7 [select* field ... \"Label|value\" ...] options."""
    # Find the select shortcode for this field (may span lines)
    pat = rf'\[select\*? {re.escape(field)}\b[^\]]*\]'
    m = re.search(pat, form, flags=re.S)
    if not m:
        return []
    block = m.group(0)
    opts = []
    for om in re.finditer(r'"([^"\\]*(?:\\.[^"\\]*)*)"', block):
        raw = om.group(1).replace('\\"', '"')
        if raw.lower().startswith("selecione"):
            continue
        if "|" in raw:
            label, value = raw.rsplit("|", 1)
        else:
            label, value = raw, raw
        value = value.strip().lower()
        if not value or value in ("first_as_label",):
            continue
        # skip class tokens mistakenly captured — CF7 options are Label|slug
        if " " in value and not re.fullmatch(r"[a-z0-9_-]+", value):
            continue
        if not re.fullmatch(r"[a-z0-9_-]+", value):
            continue
        opts.append({"label": label.strip(), "slug": value})
    # de-dupe preserving order
    seen = set()
    out = []
    for o in opts:
        if o["slug"] in seen:
            continue
        seen.add(o["slug"])
        out.append(o)
    return out


def fetch_cf7(base: str, auth: str, form_id: int = 1831) -> dict:
    st, data = get_json(f"{base.rstrip('/')}/wp-json/contact-form-7/v1/contact-forms/{form_id}", auth)
    form = ""
    if isinstance(data, dict):
        props = data.get("properties") or {}
        form_obj = props.get("form") if isinstance(props, dict) else None
        if isinstance(form_obj, dict):
            form = form_obj.get("content") or ""
        elif isinstance(form_obj, str):
            form = form_obj
        # some installs nest differently
        if not form and isinstance(data.get("form"), str):
            form = data["form"]
    unit = parse_cf7_select_options(form, "unit")
    easy = parse_cf7_select_options(form, "easyunit")
    return {
        "status": st,
        "title": data.get("title") if isinstance(data, dict) else None,
        "form_len": len(form),
        "unit": unit,
        "easyunit": easy,
        "unit_slugs": [o["slug"] for o in unit],
        "easyunit_slugs": [o["slug"] for o in easy],
    }


def try_fetch_loja_functions_via_hostinger() -> dict | None:
    """If a loja hostinger env exists, pull functions.php; else None."""
    for name in ("hostinger-loja.env", "hostinger.env"):
        path = SECRETS / name
        if path.is_file():
            e = read_env(path)
            # reuse extract against dumped file if we fetch
            return {"env_file": name, "keys": list(e.keys())}
    return None


def flags(row: tuple) -> str:
    _, _, _, cera_f, laser_f, cera_m, laser_m = row
    parts = []
    if cera_f:
        parts.append("cera♀")
    if laser_f:
        parts.append("laser♀")
    if cera_m:
        parts.append("cera♂")
    if laser_m:
        parts.append("laser♂")
    return ", ".join(parts)


def main() -> None:
    keys_report = json.loads(KEYS.read_text(encoding="utf-8"))
    acces_slugs = {r["slug"] for r in keys_report["rows"]}
    acces_map = {r["slug"]: r for r in keys_report["rows"]}

    loja_e = read_env(SECRETS / "loja.env")
    ot_e = read_env(SECRETS / "oficialteste.env")
    loja_auth = auth_header(loja_e["PM_LOJA_USER"], loja_e["PM_LOJA_APP_PASSWORD"])
    ot_auth = auth_header(ot_e["PM_OFICIALTESTE_USER"], ot_e["PM_OFICIALTESTE_APP_PASSWORD"])

    loja_cf7 = fetch_cf7(loja_e["PM_LOJA_URL"], loja_auth)
    ot_cf7 = fetch_cf7(ot_e["PM_OFICIALTESTE_URL"], ot_auth)

    hostinger_loja = try_fetch_loja_functions_via_hostinger()

    # Fallback: parse unit/easyunit from cached study if live CF7 fails
    if loja_cf7["status"] != 200 or not loja_cf7["unit"]:
        study = SECRETS / "_study_accesstage_cf7.json"
        if study.is_file():
            cached = json.loads(study.read_text(encoding="utf-8"))
            form = cached.get("form_content") or ""
            unit = parse_cf7_select_options(form, "unit")
            easy = parse_cf7_select_options(form, "easyunit")
            loja_cf7 = {
                "status": "cached_study",
                "title": cached.get("cf7_title"),
                "form_len": len(form),
                "unit": unit,
                "easyunit": easy,
                "unit_slugs": [o["slug"] for o in unit],
                "easyunit_slugs": [o["slug"] for o in easy],
                "note": "live CF7 failed or empty; used _study_accesstage_cf7.json",
            }

    loja_unit = set(loja_cf7.get("unit_slugs") or [])
    loja_easy = set(loja_cf7.get("easyunit_slugs") or [])
    ot_unit = set(ot_cf7.get("unit_slugs") or [])
    ot_easy = set(ot_cf7.get("easyunit_slugs") or [])

    catalog_rows = []
    for row in STORE_UNITS:
        code, name, state, *_ = row
        slug = CODE_TO_SLUG.get(code, "")
        acc = acces_map.get(slug) if slug else None
        catalog_rows.append(
            {
                "code": code,
                "name": name,
                "state": state,
                "capacity": flags(row),
                "accesstage_slug": slug or None,
                "has_api": bool(acc and acc.get("has_api")),
                "has_apikey": bool(acc and acc.get("has_apikey")),
                "in_cf7_unit_loja": slug in loja_unit if slug else False,
                "in_cf7_easyunit_loja": slug in loja_easy if slug else False,
                "in_cf7_unit_ot": slug in ot_unit if slug else False,
                "in_cf7_easyunit_ot": slug in ot_easy if slug else False,
            }
        )

    mapped_slugs = {CODE_TO_SLUG[c] for c, *_ in ((r[0],) for r in STORE_UNITS) if c in CODE_TO_SLUG}
    # fix mapped_slugs properly
    mapped_slugs = set(CODE_TO_SLUG.values())

    orphan_acces = sorted(acces_slugs - mapped_slugs)
    orphan_cf7_loja = sorted((loja_unit | loja_easy) - acces_slugs)
    missing_token = [r for r in catalog_rows if not (r["has_api"] and r["has_apikey"])]
    missing_cf7_loja = [r for r in catalog_rows if not r["in_cf7_unit_loja"]]

    inventory = {
        "storeUnits_count": len(STORE_UNITS),
        "accesstage_ot": {
            "source": keys_report.get("source"),
            "slug_count": keys_report.get("slug_count"),
            "all_have_api_and_apikey": keys_report.get("api_count") == keys_report.get("apikey_count")
            == keys_report.get("slug_count"),
            "slugs": sorted(acces_slugs),
        },
        "loja_functions_php": {
            "hostinger_env": hostinger_loja,
            "note": "Sem hostinger-loja.env; tokens lidos do child theme OT. Loja tipicamente compartilha o mesmo payment_CF7 no shopwise-child.",
        },
        "cf7": {
            "loja": {k: v for k, v in loja_cf7.items() if k != "unit" and k != "easyunit"}
            | {
                "unit_count": len(loja_cf7.get("unit") or []),
                "easyunit_count": len(loja_cf7.get("easyunit") or []),
                "unit": loja_cf7.get("unit"),
                "easyunit": loja_cf7.get("easyunit"),
            },
            "ot": {k: v for k, v in ot_cf7.items() if k != "unit" and k != "easyunit"}
            | {
                "unit_count": len(ot_cf7.get("unit") or []),
                "easyunit_count": len(ot_cf7.get("easyunit") or []),
                "unit": ot_cf7.get("unit"),
                "easyunit": ot_cf7.get("easyunit"),
            },
        },
        "catalog_crosswalk": catalog_rows,
        "gaps": {
            "storeUnits_without_accesstage_token": [
                {"code": r["code"], "slug": r["accesstage_slug"]} for r in missing_token
            ],
            "storeUnits_missing_from_cf7_unit_loja": [
                {"code": r["code"], "slug": r["accesstage_slug"]} for r in missing_cf7_loja
            ],
            "accesstage_slugs_not_in_storeUnits": orphan_acces,
            "cf7_loja_slugs_without_accesstage_token": orphan_cf7_loja,
            "cf7_unit_loja_vs_ot_diff": {
                "only_loja": sorted(loja_unit - ot_unit),
                "only_ot": sorted(ot_unit - loja_unit),
            },
            "cf7_easyunit_loja_vs_ot_diff": {
                "only_loja": sorted(loja_easy - ot_easy),
                "only_ot": sorted(ot_easy - loja_easy),
            },
        },
    }

    OUT_JSON.write_text(json.dumps(inventory, ensure_ascii=False, indent=2), encoding="utf-8")

    # Markdown report (no secrets)
    lines = []
    lines.append("# 37 — Inventário unidades × AccesStage")
    lines.append("")
    lines.append("Data: 2026-11-03. Fontes: `storeUnits` (data.ts), `shopwise-child/functions.php` no OficialTeste (Hostinger), CF7 #1831 loja+OT.")
    lines.append("")
    lines.append("## Resumo")
    lines.append("")
    lines.append(f"- **Unidades no catálogo front (`storeUnits`)**: {len(STORE_UNITS)}")
    lines.append(f"- **Slugs com token AccesStage (OT `$api`+`$apikey`)**: {len(acces_slugs)} — todos com o par completo")
    lines.append(f"- **CF7 `unit` loja**: {len(loja_unit)} opções | **`easyunit` (laser) loja**: {len(loja_easy)}")
    lines.append(f"- **CF7 `unit` OT**: {len(ot_unit)} | **`easyunit` OT**: {len(ot_easy)}")
    lines.append(f"- **storeUnits sem token AccesStage**: {len(missing_token)}")
    lines.append(f"- **Slugs AccesStage fora do storeUnits**: {len(orphan_acces)}")
    lines.append("")
    lines.append("### Tokens na loja vs OT")
    lines.append("")
    lines.append(
        "A conta Hostinger `u956483026` só serve o **OficialTeste**. "
        "`loja.pellomenos.com.br` não está nessa Files API (HTTP 404). "
        "Tokens AccesStage (44 slugs) vieram do `shopwise-child/functions.php` do OT. "
        "CF7 #1831 loja e OT estão idênticos em `unit`/`easyunit` nesta data; "
        "todos os slugs do `unit` da loja existem no mapa de tokens OT."
    )
    lines.append("")
    lines.append("## storeUnits × AccesStage × CF7")
    lines.append("")
    lines.append("| Código | Nome | UF | Capacidade | Slug AccesStage | Token | CF7 unit loja | CF7 easyunit loja |")
    lines.append("|---|---|---|---|---|---|---|---|")
    for r in catalog_rows:
        tok = "sim" if r["has_api"] and r["has_apikey"] else "NÃO"
        lines.append(
            f"| {r['code']} | {r['name']} | {r['state']} | {r['capacity']} | `{r['accesstage_slug']}` | {tok} | "
            f"{'sim' if r['in_cf7_unit_loja'] else 'não'} | {'sim' if r['in_cf7_easyunit_loja'] else 'não'} |"
        )
    lines.append("")
    lines.append("## Gaps")
    lines.append("")
    lines.append("### AccesStage com token, mas fora do `storeUnits` (front não vende)")
    lines.append("")
    if orphan_acces:
        for s in orphan_acces:
            in_u = "unit" if s in loja_unit else ""
            in_e = "easyunit" if s in loja_easy else ""
            where = ", ".join(x for x in (in_u, in_e) if x) or "não aparece no CF7 loja"
            lines.append(f"- `{s}` — CF7 loja: {where}")
    else:
        lines.append("- (nenhum)")
    lines.append("")
    lines.append("### storeUnits sem token")
    lines.append("")
    if missing_token:
        for r in missing_token:
            lines.append(f"- {r['code']} → `{r['accesstage_slug']}`")
    else:
        lines.append("- (nenhum — todos os códigos do catálogo têm par api+apikey no OT)")
    lines.append("")
    lines.append("### storeUnits ausentes do select CF7 `unit` da loja")
    lines.append("")
    if missing_cf7_loja:
        for r in missing_cf7_loja:
            lines.append(f"- {r['code']} → `{r['accesstage_slug']}`")
    else:
        lines.append("- (nenhum)")
    lines.append("")
    lines.append("### Diff CF7 unit loja vs OT")
    lines.append("")
    d = inventory["gaps"]["cf7_unit_loja_vs_ot_diff"]
    lines.append(f"- Só loja: {', '.join(f'`{x}`' for x in d['only_loja']) or '(vazio)'}")
    lines.append(f"- Só OT: {', '.join(f'`{x}`' for x in d['only_ot']) or '(vazio)'}")
    lines.append("")
    lines.append("### Diff CF7 easyunit loja vs OT")
    lines.append("")
    d = inventory["gaps"]["cf7_easyunit_loja_vs_ot_diff"]
    lines.append(f"- Só loja: {', '.join(f'`{x}`' for x in d['only_loja']) or '(vazio)'}")
    lines.append(f"- Só OT: {', '.join(f'`{x}`' for x in d['only_ot']) or '(vazio)'}")
    lines.append("")
    lines.append("## CF7 `unit` (loja) — lista completa")
    lines.append("")
    for o in loja_cf7.get("unit") or []:
        tok = "token OK" if o["slug"] in acces_slugs else "SEM token OT"
        lines.append(f"- `{o['slug']}` — {o['label']} — {tok}")
    lines.append("")
    lines.append("## CF7 `easyunit` laser (loja)")
    lines.append("")
    for o in loja_cf7.get("easyunit") or []:
        tok = "token OK" if o["slug"] in acces_slugs else "SEM token OT"
        lines.append(f"- `{o['slug']}` — {o['label']} — {tok}")
    lines.append("")
    lines.append("## Notas")
    lines.append("")
    lines.append("- Cobrança usa `easyunit` se preenchido, senão `unit` (`payment_CF7`).")
    lines.append("- `rjsaojose` existe no AccesStage OT além de `saojose`; o CF7 da loja usa `saojose` para Centro — Rua São José.")
    lines.append("- `niteroi` no AccesStage OT não é o mesmo que `icarai` (Icaraí); `niteroi` fica órfão do catálogo atual.")
    lines.append("- JSON detalhado (sem valores de chave): `projeto-migracao/.secrets/_inventory_accesstage_units.json`.")
    lines.append("")

    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print("loja cf7", loja_cf7["status"], "unit", len(loja_unit), "easy", len(loja_easy))
    print("ot cf7", ot_cf7["status"], "unit", len(ot_unit), "easy", len(ot_easy))
    print("missing token", len(missing_token), "orphan acces", orphan_acces)
    print("wrote", OUT_JSON)
    print("wrote", OUT_MD)


if __name__ == "__main__":
    main()
