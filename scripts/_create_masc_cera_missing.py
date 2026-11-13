# -*- coding: utf-8 -*-
"""
Create the 10 missing masculine cera products on oficialteste Woo +
wire Next seeds (data.ts) and woo-bridge.json.

Loja = never written. Woo variation price = R$ 1,00 (oficialteste test),
bridge/seeds = table ecommerce prices (skipDiscount).
"""
from __future__ import annotations

import base64
import json
import shutil
import urllib.error
import urllib.request
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV = ROOT / "projeto-migracao" / ".secrets" / "oficialteste.env"
DATA = ROOT / "src" / "lib" / "data.ts"
BRIDGE = ROOT / "src" / "lib" / "woo-bridge.json"
BRIDGE_WP = ROOT / "wordpress-loja" / "pm-home" / "woo-bridge.json"
REPORT = ROOT / "projeto-migracao" / ".secrets" / "masc-cera-created-report.md"
IMG_DIR = ROOT / "public" / "images" / "products" / "male"
IMG_FEM = ROOT / "public" / "images" / "products"

# Catalog id → (name, cents, category, duration, description, image_source)
NEW_PRODUCTS: dict[str, dict] = {
    "barba-cera-masc": {
        "name": "Barba – Cera",
        "cents": 5690,
        "category": "rosto",
        "duration": "20 min • Avulso",
        "description": "Depilação a cera da barba masculina: remove os pelos da região da barba pela raiz.",
        "image_from": "barba-laser-masc.png",
        "woo_name": "Barba – Cera Masculino",
    },
    "barba-modeladora-cera-masc": {
        "name": "Barba Modeladora – Cera",
        "cents": 7490,
        "category": "rosto",
        "duration": "25 min • Avulso",
        "description": "Modelagem da barba com cera: desenho e limpeza das linhas para valorizar o contorno.",
        "image_from": "barba-laser-masc.png",
        "woo_name": "Barba Modeladora – Cera Masculino",
    },
    "bigode-cera-masc": {
        "name": "Bigode – Cera",
        "cents": 3850,
        "category": "rosto",
        "duration": "10 min • Avulso",
        "description": "Depilação a cera do bigode masculino: remove os pelos da região do bigode.",
        "image_from": "bigode-laser-masc.png",
        "woo_name": "Bigode – Cera Masculino",
    },
    "orelha-cera-masc": {
        "name": "Orelha – Cera",
        "cents": 3290,
        "category": "rosto",
        "duration": "10 min • Avulso",
        "description": "Depilação a cera das orelhas masculinas: remove os pelos da orelha e entrada do canal.",
        "image_from": "orelhas-laser-masc.png",
        "woo_name": "Orelha – Cera Masculino",
    },
    "pescoco-cera-masc": {
        "name": "Pescoço – Cera",
        "cents": 3290,
        "category": "rosto",
        "duration": "10 min • Avulso",
        "description": "Depilação a cera do pescoço masculino: remove os pelos da região do pescoço.",
        "image_from": "pescoco-laser-masc.png",
        "woo_name": "Pescoço – Cera Masculino",
    },
    "mamilos-cera-masc": {
        "name": "Mamilos – Cera",
        "cents": 3290,
        "category": "torax",
        "duration": "10 min • Avulso",
        "description": "Depilação a cera dos mamilos masculinos: remove os pelos ao redor dos mamilos.",
        "image_from": "mamilo-laser-masc.png",
        "woo_name": "Mamilos – Cera Masculino",
    },
    "sobrancelha-cera-masc": {
        "name": "Sobrancelha – Cera",
        "cents": 5290,
        "category": "sobrancelha",
        "duration": "15 min • Avulso",
        "description": "Depilação de sobrancelha masculina com cera: limpeza conforme o desenho já existente.",
        "image_from_fem": "sobrancelha-cera.png",
        "woo_name": "Sobrancelha – Cera Masculino",
    },
    "design-sobrancelha-masc": {
        "name": "Design de Sobrancelha – Cera",
        "cents": 6990,
        "category": "sobrancelha",
        "duration": "20 min • Avulso",
        "description": "Design de sobrancelha masculino com cera: remodela o desenho para valorizar o olhar.",
        "image_from_fem": "design-sobrancelha.png",
        "woo_name": "Design de Sobrancelha – Cera Masculino",
    },
    "torax-abdomen-cera-masc": {
        "name": "Tórax + Abdômen – Cera",
        "cents": 8990,
        "category": "torax",
        "duration": "35 min • Avulso",
        "description": "Combo peito e abdômen a cera: remove os pelos do tórax e da parede abdominal.",
        "image_from": "torax-abdomen-laser-masc.png",
        "woo_name": "Tórax + Abdômen – Cera Masculino",
    },
    "saco-escrotal-cera-masc": {
        "name": "Saco Escrotal – Cera",
        "cents": 5890,
        "category": "virilha",
        "duration": "15 min • Avulso",
        "description": "Depilação a cera do saco escrotal: remove os pelos da região do saco.",
        "image_from": "virilha-comum-cera-masc.png",
        "woo_name": "Saco Escrotal – Cera Masculino",
    },
}

MASC_CERA_CATEGORY_ID = 147
ATTR_UNIDADE_ID = 4
TEMPLATE_BRIDGE_KEY = "queixo-cera-masc"
LONG_TEXT = (
    "Serviço de depilação a cera masculino no Pello Menos.\n\n"
    "A imagem do serviço é meramente ilustrativa. O valor muda conforme a unidade, "
    "porque São Paulo capital e DF têm outra tabela.\n\n"
    "Compras na loja on-line somente poderão ser utilizadas após 24 horas, "
    "a contar da confirmação do pagamento. Prazo de utilização de até 90 dias."
)


def load_env():
    values = {}
    for line in ENV.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        values[k.strip()] = v.strip()
    return {
        "url": values["PM_OFICIALTESTE_URL"].rstrip("/"),
        "user": values["PM_OFICIALTESTE_USER"],
        "password": values["PM_OFICIALTESTE_APP_PASSWORD"],
    }


def api(cfg, method: str, path: str, body=None):
    headers = {
        "Authorization": "Basic "
        + base64.b64encode(f"{cfg['user']}:{cfg['password']}".encode()).decode(),
        "Accept": "application/json",
        "User-Agent": "pm-create-masc-cera/1.0",
    }
    data = None
    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(cfg["url"] + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            raw = r.read().decode("utf-8", "replace")
            return r.status, json.loads(raw) if raw.strip() else {}
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", "replace")
        try:
            parsed = json.loads(raw)
        except Exception:
            parsed = raw[:800]
        raise SystemExit(f"HTTP {e.code} {method} {path}: {parsed}")


def ensure_images():
    IMG_DIR.mkdir(parents=True, exist_ok=True)
    for pid, meta in NEW_PRODUCTS.items():
        dest = IMG_DIR / f"{pid}.png"
        if dest.exists():
            continue
        if "image_from" in meta:
            src = IMG_DIR / meta["image_from"]
        else:
            src = IMG_FEM / meta["image_from_fem"]
        if not src.exists():
            raise SystemExit(f"missing image source {src} for {pid}")
        shutil.copyfile(src, dest)
        print("image", dest.name, "<-", src.name)


def seed_block() -> str:
    lines = [
        "",
        "  // Cera masculino — áreas novas (tabela Rafael; skipDiscount; Woo próprio no oficialteste)",
    ]
    for pid, meta in NEW_PRODUCTS.items():
        badge = ""
        if pid in ("barba-cera-masc", "design-sobrancelha-masc", "torax-abdomen-cera-masc"):
            badge = ', badge: "Cera", highlight: true'
        elif pid in ("sobrancelha-cera-masc", "saco-escrotal-cera-masc"):
            badge = ', badge: "Cera"'
        lines.append(
            "  { "
            f'id: "{pid}", name: "{meta["name"]}", duration: "{meta["duration"]}", '
            f'originalCents: {meta["cents"]}, skipDiscount: true, category: "{meta["category"]}", '
            f'image: catalogImage("{pid}", "masculino"), '
            f'imageAlt: "{meta["name"]} Pello Menos", '
            f'description: "{meta["description"]}", '
            f'method: "cera", audience: "masculino"{badge} '
            "},"
        )
    return "\n".join(lines) + "\n"


def patch_data_ts():
    text = DATA.read_text(encoding="utf-8")
    marker = "  // Esfoliação masculino — tabela Rafael"
    if "barba-cera-masc" in text:
        print("data.ts already has barba-cera-masc — skip seed insert")
    else:
        if marker not in text:
            raise SystemExit("esfoliação masc marker not found in data.ts")
        text = text.replace(marker, seed_block() + marker, 1)
        print("patched data.ts seeds")

    # Expand ceraAreasMasc highlight list with new face/body items
    old = '''  ceraAreasMasc: male.filter((item) =>
    [
      "virilha-cera-masc",
      "axila-cera-masc",
      "perna-cera-masc",
      "peito-cera-masc",
      "meia-nadega-cera-masc",
      "meia-perna-cera-masc",
      "coxa-cera-masc",
      "bracos-cera-masc",
      "virilha-comum-cera-masc",
      "nadegas-cera-masc",
      "queixo-cera-masc",
      "costas-cera-masc",
      "abdomen-cera-masc",
    ].includes(item.id),
  ),'''
    new = '''  ceraAreasMasc: male.filter((item) =>
    [
      "virilha-cera-masc",
      "axila-cera-masc",
      "perna-cera-masc",
      "peito-cera-masc",
      "meia-nadega-cera-masc",
      "meia-perna-cera-masc",
      "coxa-cera-masc",
      "bracos-cera-masc",
      "virilha-comum-cera-masc",
      "nadegas-cera-masc",
      "queixo-cera-masc",
      "costas-cera-masc",
      "abdomen-cera-masc",
      "barba-cera-masc",
      "bigode-cera-masc",
      "torax-abdomen-cera-masc",
      "saco-escrotal-cera-masc",
      "sobrancelha-cera-masc",
      "design-sobrancelha-masc",
    ].includes(item.id),
  ),'''
    if "barba-cera-masc" not in text.split("ceraAreasMasc")[1].split("esfoliacaoMasc")[0]:
        if old not in text:
            raise SystemExit("ceraAreasMasc block not found")
        text = text.replace(old, new, 1)
        print("patched ceraAreasMasc")
    else:
        print("ceraAreasMasc already updated")

    DATA.write_text(text, encoding="utf-8")


def find_by_slug(cfg, slug: str):
    status, data = api(cfg, "GET", f"/wp-json/wc/v3/products?slug={slug}&per_page=1")
    if isinstance(data, list) and data:
        return data[0]
    return None


def create_woo_product(cfg, catalog_id: str, meta: dict, unit_options: list[str]):
    existing = find_by_slug(cfg, catalog_id)
    if existing:
        print("woo exists", catalog_id, existing["id"])
        return existing

    payload = {
        "name": meta["woo_name"],
        "type": "variable",
        "status": "publish",
        "catalog_visibility": "visible",
        "description": LONG_TEXT,
        "short_description": meta["description"],
        "slug": catalog_id,
        "categories": [{"id": MASC_CERA_CATEGORY_ID}],
        "attributes": [
            {
                "id": ATTR_UNIDADE_ID,
                "name": "Unidade",
                "visible": True,
                "variation": True,
                "options": unit_options,
            }
        ],
    }
    status, created = api(cfg, "POST", "/wp-json/wc/v3/products", payload)
    print("woo created", catalog_id, created.get("id"), "http", status)
    return created


def list_variations(cfg, product_id: int):
    status, data = api(
        cfg, "GET", f"/wp-json/wc/v3/products/{product_id}/variations?per_page=100"
    )
    return data if isinstance(data, list) else []


def ensure_variations(cfg, product_id: int, units: dict[str, dict]):
    existing = list_variations(cfg, product_id)
    by_option = {}
    for v in existing:
        attrs = v.get("attributes") or []
        opt = attrs[0].get("option") if attrs else None
        if opt:
            by_option[opt] = v

    result_units = {}
    for unit_id, meta in units.items():
        option = meta["option"]
        if option in by_option:
            vid = by_option[option]["id"]
        else:
            payload = {
                "regular_price": "1.00",
                "status": "publish",
                "stock_status": "instock",
                "manage_stock": False,
                "attributes": [
                    {
                        "id": ATTR_UNIDADE_ID,
                        "name": "Unidade",
                        "option": option,
                    }
                ],
            }
            status, created = api(
                cfg, "POST", f"/wp-json/wc/v3/products/{product_id}/variations", payload
            )
            vid = created["id"]
            print("  var", unit_id, vid, option[:40])
        result_units[unit_id] = {"variationId": vid, "option": option}
    return result_units


def patch_bridge(created_map: dict[str, dict]):
    bridge = json.loads(BRIDGE.read_text(encoding="utf-8"))
    template = bridge[TEMPLATE_BRIDGE_KEY]
    template_units = template["units"]

    for pid, info in created_map.items():
        cents = NEW_PRODUCTS[pid]["cents"]
        row = {
            "slug": pid,
            "productId": info["productId"],
            "longText": LONG_TEXT,
            "rj": {"regularCents": cents, "saleCents": cents},
            "spdf": {"regularCents": cents, "saleCents": cents},
            "units": info["units"],
        }
        bridge[pid] = row
        print("bridge", pid, "productId", info["productId"], "units", len(info["units"]))

    BRIDGE.write_text(json.dumps(bridge, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    shutil.copyfile(BRIDGE, BRIDGE_WP)
    print("copied bridge to WP")


def write_report(created_map: dict[str, dict]):
    lines = [
        "# Produtos cera masculinos criados (oficialteste)",
        "",
        "Woo: preço variação R$ 1,00 (teste). Seeds/bridge: preço tabela Rafael (`skipDiscount`).",
        "",
        "| ID | Woo productId | Preço tabela | Unidades |",
        "|----|---------------|--------------|----------|",
    ]
    for pid, info in created_map.items():
        cents = NEW_PRODUCTS[pid]["cents"]
        price = f"{cents/100:.2f}".replace(".", ",")
        lines.append(f"| `{pid}` | {info['productId']} | R$ {price} | {len(info['units'])} |")
    lines.append("")
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print("report", REPORT)


def main():
    cfg = load_env()
    if "loja.pellomenos.com.br" in cfg["url"]:
        raise SystemExit("refusing to write to loja")

    ensure_images()
    patch_data_ts()

    bridge = json.loads(BRIDGE.read_text(encoding="utf-8"))
    template_units = bridge[TEMPLATE_BRIDGE_KEY]["units"]
    unit_options = [u["option"] for u in template_units.values()]

    created_map = {}
    for pid, meta in NEW_PRODUCTS.items():
        product = create_woo_product(cfg, pid, meta, unit_options)
        pid_woo = product["id"]
        units = ensure_variations(cfg, pid_woo, template_units)
        created_map[pid] = {"productId": pid_woo, "units": units}

    patch_bridge(created_map)
    write_report(created_map)
    print("DONE", len(created_map))


if __name__ == "__main__":
    main()
