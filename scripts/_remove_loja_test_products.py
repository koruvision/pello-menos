# -*- coding: utf-8 -*-
"""Remove SKUs de teste (1,99 + esquenta) do front pm-home e do catálogo Next."""
import io
import json
import re
import sys
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PM = ROOT / "wordpress-loja" / "pm-home"
ENV = ROOT / "projeto-migracao" / ".secrets" / "loja.env"

TEST_IDS = [
    "produto-1-real",
    "pm-teste-esquenta-laser",
    "pm-teste-esquenta-laser-b",
    "pm-teste-esquenta-laser-c",
    "pm-teste-esquenta-cera",
    "pm-teste-esquenta-cera-b",
    "pm-teste-esquenta-cera-c",
]
ALIAS_ROUTES = ["produto-r-1"]


def env():
    values = {}
    for line in ENV.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        values[k.strip()] = v.strip()
    return values


def call(method, path, payload=None, raw=None, content_type="application/json", timeout=120):
    cfg = env()
    import base64

    token = base64.b64encode(
        f"{cfg['PM_LOJA_USER']}:{cfg['PM_LOJA_APP_PASSWORD']}".encode()
    ).decode()
    data = raw if raw is not None else (
        None if payload is None else json.dumps(payload).encode("utf-8")
    )
    req = urllib.request.Request(
        cfg["PM_LOJA_URL"].rstrip("/") + path,
        data=data,
        method=method,
        headers={
            "User-Agent": "pm-remove-test/1.0",
            "Authorization": "Basic " + token,
            "Content-Type": content_type,
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", "replace")
            return resp.status, (json.loads(body) if body[:1] in "[{" else body)
    except urllib.error.HTTPError as error:
        body = error.read().decode("utf-8", "replace")
        return error.code, (json.loads(body) if body[:1] in "[{" else body[:800])


def drop_keys(obj, keys):
    if not isinstance(obj, dict):
        return obj
    for k in keys:
        obj.pop(k, None)
    return obj


def clean_json_file(path, keys):
    if not path.is_file():
        return
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        # cart-related may nest under a key
        if all(k in data for k in ("produto-1-real",) if False):
            pass
        drop_keys(data, keys)
        # nested maps (cart-related structure)
        for top in list(data.keys()):
            if isinstance(data[top], dict):
                drop_keys(data[top], keys)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("cleaned", path.relative_to(ROOT))


def clean_data_ts():
    path = ROOT / "src" / "lib" / "data.ts"
    text = path.read_text(encoding="utf-8")
    # remove the produto-1-real seed object
    pattern = re.compile(
        r"\n  \{\n    id: \"produto-1-real\",[\s\S]*?\n  \},\n",
        re.M,
    )
    new, n = pattern.subn("\n", text, count=1)
    if n != 1:
        raise SystemExit("produto-1-real seed not found in data.ts")
    new = new.replace(
        "/** Override global de cobrança (0 = preços reais de catálogo/bridge). SKU `produto-1-real` fica R$ 1,99 no seed. */",
        "/** Override global de cobrança (0 = preços reais de catálogo/bridge). */",
    )
    new = new.replace(
        'productsByMethod(audience, method).find((item) => item.id !== "produto-1-real")',
        "productsByMethod(audience, method)[0]",
    )
    path.write_text(new, encoding="utf-8")
    print("data.ts OK")


def clean_black_nov():
    path = ROOT / "src" / "lib" / "black-nov-campaign.ts"
    text = path.read_text(encoding="utf-8")
    text2 = text.replace(', "produto-1-real"', "")
    if text2 != text:
        path.write_text(text2, encoding="utf-8")
        print("black-nov exclude cleaned")


def clean_home():
    path = PM / "home.html"
    text = path.read_text(encoding="utf-8")
    text2, n = re.subn(
        r'<section id="ensaio-testes"[\s\S]*?</section>',
        "",
        text,
        count=1,
    )
    for pid in TEST_IDS:
        text2 = text2.replace(f"/produto/{pid}/", "/loja/")
        text2 = text2.replace(f"/produto/{pid}", "/loja/")
    path.write_text(text2, encoding="utf-8")
    print("home ensaio removed", n, "still test refs", sum(text2.count(x) for x in TEST_IDS))


def delete_product_files():
    for pid in TEST_IDS:
        for path in [
            PM / "products" / f"{pid}.html",
            ROOT / "src" / "lib" / "product-copy.json",
        ]:
            pass
        p = PM / "products" / f"{pid}.html"
        if p.is_file():
            p.unlink()
            print("deleted", p.name)


def clean_product_copy():
    path = ROOT / "src" / "lib" / "product-copy.json"
    if not path.is_file():
        return
    data = json.loads(path.read_text(encoding="utf-8"))
    changed = False
    for pid in TEST_IDS:
        if pid in data:
            del data[pid]
            changed = True
    if changed:
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print("product-copy cleaned")


def draft_woo_products():
    # collect woo ids from bridge before deletion
    bridge_path = PM / "woo-bridge.json"
    bridge = json.loads(bridge_path.read_text(encoding="utf-8"))
    ids = []
    for pid in TEST_IDS:
        info = bridge.get(pid) or {}
        wid = info.get("productId") or info.get("id")
        if wid:
            ids.append((pid, int(wid)))
    # also known from json
    skus = ROOT / "scripts" / "_loja_esquenta_test_skus.json"
    if skus.is_file():
        for pid, wid in json.loads(skus.read_text(encoding="utf-8")).items():
            ids.append((pid, int(wid)))
    # cheap product 49394
    ids.append(("produto-r-1", 49394))
    seen = set()
    for pid, wid in ids:
        if wid in seen:
            continue
        seen.add(wid)
        st, body = call(
            "PUT",
            f"/wp-json/wc/v3/products/{wid}",
            {"status": "draft", "catalog_visibility": "hidden"},
        )
        print("woo draft", pid, wid, st, body.get("status") if isinstance(body, dict) else body)


def publish_bundle():
    cfg = env()
    dest_base = cfg["PM_LOJA_URL"].rstrip("/") + "/wp-content/uploads/pm-home"
    clone_base = "https://pellomenos.companygenesis.com.br/wp-content/uploads/pm-home"
    files = [
        "home.html",
        "woo-bridge.json",
        "cart-related.json",
        "routes.json",
        "busca.html",
        "busca.js",
    ]
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for rel in files:
            path = PM / rel
            text = path.read_text(encoding="utf-8")
            text = text.replace(clone_base, dest_base)
            z.writestr(rel, text.encode("utf-8"))
            print("zip+", rel)
        # also delete remote product files by uploading empty? plugin may not delete.
        # overwrite with redirect stub pages that say removed
        stub = (
            "<!doctype html><meta charset=utf-8>"
            "<meta http-equiv=refresh content='0;url=/loja/'>"
            "<title>Removido</title><p>Produto de teste removido. <a href=/loja/>Loja</a></p>"
        )
        for pid in TEST_IDS:
            z.writestr(f"products/{pid}.html", stub.encode("utf-8"))
            print("zip+ stub", pid)
    st, body = call(
        "POST",
        "/wp-json/pm-home/v1/bundle",
        raw=buf.getvalue(),
        content_type="application/zip",
        timeout=600,
    )
    print("bundle", st, body if isinstance(body, dict) else str(body)[:300])
    if st != 200:
        raise SystemExit("bundle failed")


def smoke():
    cfg = env()
    base = cfg["PM_LOJA_URL"].rstrip("/")

    def get(url):
        req = urllib.request.Request(url, headers={"User-Agent": "pm-remove-smoke"})
        with urllib.request.urlopen(req, timeout=60) as resp:
            return resp.read().decode("utf-8", "replace")

    home = get(base + "/wp-content/uploads/pm-home/home.html?v=notest1")
    print(
        "home",
        "ensaio" in home,
        "produto-1-real",
        "produto-1-real" in home,
        "pm-teste",
        "pm-teste-esquenta" in home,
    )
    busca = get(base + "/busca?q=teste")
    print("busca cards still mention 1 real?", "Produto R$ 1,99" in busca)
    if "ensaio-testes" in home or "produto-1-real" in home:
        raise SystemExit("test products still on home")


def main():
    clean_data_ts()
    clean_black_nov()
    clean_product_copy()
    clean_home()
    delete_product_files()

    for path in [
        PM / "woo-bridge.json",
        ROOT / "src" / "lib" / "woo-bridge.json",
        PM / "cart-related.json",
        PM / "routes.json",
    ]:
        keys = TEST_IDS + ALIAS_ROUTES
        data = json.loads(path.read_text(encoding="utf-8"))
        if path.name == "cart-related.json":
            products = data.get("products")
            if isinstance(products, dict):
                for tid in TEST_IDS:
                    products.pop(tid, None)
            cross = data.get("crossSell")
            if isinstance(cross, dict):
                for tid in TEST_IDS:
                    cross.pop(tid, None)
                for key, vals in list(cross.items()):
                    if isinstance(vals, list):
                        cross[key] = [x for x in vals if x not in TEST_IDS]
        else:
            drop_keys(data, keys)
        path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print("cleaned", path.relative_to(ROOT))

    # draft woo first while bridge still had ids — already cleaned; use known ids
    # re-load was cleaned; draft via known list
    known = [
        ("produto-1-real", 49394),
        ("pm-teste-esquenta-laser", 49387),
        ("pm-teste-esquenta-laser-b", 49388),
        ("pm-teste-esquenta-laser-c", 49389),
        ("pm-teste-esquenta-cera", 49390),
        ("pm-teste-esquenta-cera-b", 49391),
        ("pm-teste-esquenta-cera-c", 49392),
    ]
    for pid, wid in known:
        st, body = call(
            "PUT",
            f"/wp-json/wc/v3/products/{wid}",
            {"status": "draft", "catalog_visibility": "hidden"},
        )
        print("woo draft", pid, wid, st, body.get("status") if isinstance(body, dict) else body)

    # re-export busca without test products (next server)
    try:
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "export_busca", ROOT / "scripts" / "_export_busca_only.py"
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        mod.main()
    except Exception as exc:
        print("busca export skip/fail", exc)

    publish_bundle()
    smoke()
    print("TEST_PRODUCTS_REMOVED")


if __name__ == "__main__":
    main()
