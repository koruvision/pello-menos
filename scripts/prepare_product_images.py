"""Download unique WooCommerce refs and assign 1:1 images to products that uniquely own a URL."""
from __future__ import annotations

import hashlib
import json
import urllib.request
from collections import defaultdict
from io import BytesIO
from pathlib import Path
from urllib.parse import quote, urlsplit, urlunsplit

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
WC = json.loads((ROOT / "scripts" / "wc_catalog.json").read_text(encoding="utf-8"))
REF = ROOT / "public" / "images" / "ref"
FEM = ROOT / "public" / "images" / "products"
MALE = FEM / "male"
REF.mkdir(parents=True, exist_ok=True)
FEM.mkdir(parents=True, exist_ok=True)
MALE.mkdir(parents=True, exist_ok=True)

UA = {"User-Agent": "Mozilla/5.0 (compatible; PelloMenosCatalog/1.0)"}


def url_key(url: str) -> str:
    return hashlib.sha1(url.encode("utf-8")).hexdigest()[:12]


def encode_url(url: str) -> str:
    parts = urlsplit(url)
    path = quote(parts.path, safe="/-_.~")
    return urlunsplit((parts.scheme, parts.netloc, path, parts.query, parts.fragment))


def fetch(url: str) -> bytes:
    req = urllib.request.Request(encode_url(url), headers=UA)
    with urllib.request.urlopen(req, timeout=45) as res:
        return res.read()


def to_square_png(data: bytes, dest: Path) -> None:
    im = Image.open(BytesIO(data)).convert("RGB")
    w, h = im.size
    side = min(w, h)
    left = (w - side) // 2
    top = (h - side) // 2
    im = im.crop((left, top, left + side, top + side)).resize((1200, 1200), Image.Resampling.LANCZOS)
    dest.parent.mkdir(parents=True, exist_ok=True)
    im.save(dest, "PNG", optimize=True)


def main() -> None:
    by_url: dict[str, list[str]] = defaultdict(list)
    for p in WC["products"]:
        url = (p.get("imageUrl") or "").strip()
        if url:
            by_url[url].append(p["id"])

    unique_ok = []
    shared = []
    for url, ids in by_url.items():
        if len(ids) == 1:
            unique_ok.append((url, ids[0]))
        else:
            shared.append((url, ids))

    print("unique urls", len(unique_ok), "shared urls", len(shared), "shared skus", sum(len(i) for _, i in shared))

    failed = []
    for url, pid in unique_ok:
        dest = FEM / f"{pid}.png"
        if dest.exists() and dest.stat().st_size > 20_000:
            print("skip unique", pid)
            continue
        try:
            data = fetch(url)
            ref_path = REF / f"{url_key(url)}.jpg"
            Image.open(BytesIO(data)).convert("RGB").save(ref_path, "JPEG", quality=90)
            to_square_png(data, dest)
            print("ok unique", pid, dest.stat().st_size)
        except Exception as exc:
            failed.append(pid)
            print("FAIL unique", pid, type(exc).__name__, str(exc)[:160])

    # Always store shared refs too, for generation
    for url, ids in shared:
        ref_path = REF / f"{url_key(url)}.jpg"
        if ref_path.exists() and ref_path.stat().st_size > 8_000:
            print("skip ref", ids[0])
            continue
        try:
            data = fetch(url)
            Image.open(BytesIO(data)).convert("RGB").save(ref_path, "JPEG", quality=90)
            print("ok ref", url_key(url), "for", ",".join(ids[:4]))
        except Exception as exc:
            print("FAIL ref", ids, type(exc).__name__, str(exc)[:160])

    missing = []
    for p in WC["products"]:
        dest = FEM / f"{p['id']}.png"
        if not dest.exists():
            missing.append(p["id"])
    report = ROOT / "scripts" / "images_missing.json"
    report.write_text(json.dumps({"uniqueAssigned": [i for _, i in unique_ok], "missingCsv": missing, "shared": shared, "failed": failed}, ensure_ascii=False, indent=2), encoding="utf-8")
    print("missing csv", len(missing), "failed", failed)


if __name__ == "__main__":
    main()
