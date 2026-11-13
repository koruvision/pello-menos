"""Baixa as fotos oficiais do Drive, gera WebP e aponta o catálogo."""

from __future__ import annotations

import json
import re
import sys
import unicodedata
import urllib.request
from io import BytesIO
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "src" / "lib" / "data.ts"
PRODUCTS = ROOT / "public" / "images" / "products"
REPORT = ROOT / "scripts" / "_drive_image_report.json"

# Pasta pai partilhada (FEMININO / MASCULINO dentro).
DRIVE_PARENT = "1UMmUhjwJmyYfz8O6O-g0DpNB1Wp6GC29"
# Fallback se o listing da pasta pai falhar.
DRIVE_ROOTS_FALLBACK = {
    "feminino": "1NRBF0x9A5ps8_Ok7YiQOqeXiqTi7Xseo",
    "masculino": "1HVGihsGkblUqhxELV5AJTWEIzoosYV1j",
}
IMAGE_EXT = {".png", ".jpg", ".jpeg", ".webp"}
UA = {"User-Agent": "Mozilla/5.0"}


def resolve_drive_roots() -> dict[str, str]:
    roots: dict[str, str] = {}
    try:
        for file_id, name in list_folder(DRIVE_PARENT):
            upper = name.upper()
            if "FEMININO" in upper:
                roots["feminino"] = file_id
            elif "MASCULINO" in upper:
                roots["masculino"] = file_id
    except Exception as err:
        print(f"drive parent list fail: {err}", flush=True)
    if "feminino" in roots and "masculino" in roots:
        print(
            f"drive roots parent={DRIVE_PARENT} fem={roots['feminino']} masc={roots['masculino']}",
            flush=True,
        )
        return roots
    print("drive roots fallback", flush=True)
    return dict(DRIVE_ROOTS_FALLBACK)


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=120) as resp:
        return resp.read()


def list_folder(folder_id: str) -> list[tuple[str, str]]:
    html = fetch(f"https://drive.google.com/drive/folders/{folder_id}").decode(
        "utf-8", "ignore"
    )
    match = re.search(r"window\['_DRIVE_ivd'\] = '(.+?)';if", html)
    if not match:
        return []
    blob = match.group(1).encode("utf-8").decode("unicode_escape")
    return re.findall(
        r'\["([0-9A-Za-z_-]{20,})",\["'
        + re.escape(folder_id)
        + r'"\],"([^"]+)"',
        blob,
    )


def walk(folder_id: str, audience: str, trail: str) -> list[dict]:
    found: list[dict] = []
    for file_id, name in list_folder(folder_id):
        ext = Path(name).suffix.lower()
        if ext in IMAGE_EXT:
            found.append(
                {
                    "id": file_id,
                    "name": name,
                    "audience": audience,
                    "folder": trail,
                }
            )
        else:
            found.extend(walk(file_id, audience, f"{trail}/{name}"))
    return found


def slug(name: str) -> str:
    stem = Path(name).stem
    text = unicodedata.normalize("NFKD", stem)
    text = text.encode("ascii", "ignore").decode()
    text = text.lower().replace("+", " ")
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return text


ALIASES = {
    "design-de-sobrancelha-realce": "design-sobrancelha-realce",
    "design-de-sobrancelha": "design-sobrancelha",
    "perna-inteira": "perna",
    "nadegas-completas": "nadegas",
    "mamilos": "seios",
    "mamilo": "seios",
    "tintura-de-pelos-pubianos": "tintura-pelos-pubianos",
    "tintura-pelos-pubianos": "tintura-pelos-pubianos",
    "tintura-pubianos": "tintura-pelos-pubianos",
    "sobrancelha": "sobrancelha-cera",
    "sobrancelha-realce": "sobrancelha-realce-cera",
    "henna": "henna",
    "realce": "realce",
    "sobrancelha-henna": "sobrancelha-henna",
}


def folder_method(folder: str) -> str:
    text = folder.lower()
    if "esfol" in text:
        return "esfoliacao"
    if "laser" in text:
        return "laser"
    if "linha" in text:
        return "linha"
    if "cera" in text:
        return "cera"
    return ""


def product_ids() -> dict[str, str]:
    text = DATA.read_text(encoding="utf-8")
    found: dict[str, str] = {}
    for match in re.finditer(
        r'catalogImage\("([^"]+)"(?:\s*,\s*"(masculino)")?\)', text
    ):
        pid, audience = match.group(1), match.group(2) or "feminino"
        found[pid] = audience
    # Também ids de produto (para Drive → ficheiro dedicado mesmo com alias de imagem).
    for match in re.finditer(
        r'\{\s*id:\s*"([^"]+)"[\s\S]*?audience:\s*"(masculino)"',
        text,
    ):
        found.setdefault(match.group(1), "masculino")
    for match in re.finditer(r'\{\s*id:\s*"([^"]+)"', text):
        found.setdefault(match.group(1), "feminino")
    return found


def is_gift_card(pid: str) -> bool:
    """Gift cards mantêm arte local; não forçar Drive."""
    return pid.startswith("cartao-presente")


def target_id(file: dict, ids: dict[str, str]) -> str | None:
    if slug(file["name"]).startswith("magnific"):
        return None
    stem = ALIASES.get(slug(file["name"]), slug(file["name"]))
    method = folder_method(file["folder"])
    audience = file["audience"]
    stems = [stem]
    if method and method not in stem and not stem.endswith("-masc"):
        stems.append(f"{stem}-{method}")
    candidates: list[str] = []
    for item in stems:
        if audience == "masculino":
            candidates.append(item if item.endswith("-masc") else f"{item}-masc")
        candidates.append(item)
    for candidate in candidates:
        if candidate in ids and ids[candidate] == audience:
            return candidate
    return None


def download(file_id: str) -> bytes:
    url = f"https://drive.google.com/uc?export=download&confirm=t&id={file_id}"
    data = fetch(url)
    if data[:20].lstrip().startswith(b"<!DOCTYPE") or data[:15].lstrip().startswith(b"<html"):
        raise RuntimeError(f"html instead of image for {file_id}")
    return data


def to_webp(data: bytes, dest: Path) -> tuple[int, int]:
    image = Image.open(BytesIO(data))
    image = image.convert("RGB")
    width, height = image.size
    scale = min(1080 / width, 1350 / height, 1)
    if scale < 1:
        image = image.resize(
            (round(width * scale), round(height * scale)),
            Image.Resampling.LANCZOS,
        )
    dest.parent.mkdir(parents=True, exist_ok=True)
    image.save(dest, "WEBP", quality=82, method=6)
    return image.size


def existing_sources(pid: str, audience: str) -> list[Path]:
    folder = PRODUCTS / "male" if audience == "masculino" else PRODUCTS
    return [
        path
        for path in folder.glob(pid + ".*")
        if path.suffix.lower() in IMAGE_EXT and path.suffix.lower() != ".webp"
    ]


def main() -> None:
    ids = product_ids()
    files: list[dict] = []
    for audience, folder_id in resolve_drive_roots().items():
        files.extend(walk(folder_id, audience, audience.upper()))
    print(f"drive files {len(files)} catalog {len(ids)}", flush=True)
    if "--list" in sys.argv:
        lines = []
        for file in files:
            pid = target_id(file, ids)
            lines.append(f"{'OK' if pid else '??'} {pid or '-'} <= {file['folder']}/{file['name']}")
        (ROOT / "scripts" / "_drive_image_map.txt").write_text(
            "\n".join(lines), encoding="utf-8"
        )
        print("mapped", sum(1 for f in files if target_id(f, ids)), "of", len(files))
        return

    replaced: list[dict] = []
    unmatched_files: list[str] = []
    used: set[str] = set()

    skipped_gift: list[str] = []

    for file in files:
        pid = target_id(file, ids)
        if not pid:
            unmatched_files.append(f"{file['folder']}/{file['name']}")
            continue
        if is_gift_card(pid):
            if pid not in skipped_gift:
                skipped_gift.append(pid)
            used.add(pid)
            continue
        if pid in used:
            continue
        audience = ids[pid]
        folder = PRODUCTS / "male" if audience == "masculino" else PRODUCTS
        dest = folder / f"{pid}.webp"
        try:
            raw = download(file["id"])
            size = to_webp(raw, dest)
        except Exception as error:
            unmatched_files.append(f"ERRO {file['folder']}/{file['name']}: {error}")
            print(f"fail {file['name']} {error}", flush=True)
            continue
        for old in existing_sources(pid, audience):
            old.unlink()
        used.add(pid)
        replaced.append(
            {
                "id": pid,
                "from": f"{file['folder']}/{file['name']}",
                "webp": str(dest.relative_to(ROOT)).replace("\\", "/"),
                "px": size,
                "bytes": dest.stat().st_size,
            }
        )
        print(f"ok {pid} {dest.stat().st_size}", flush=True)

    kept: list[str] = []
    for pid, audience in sorted(ids.items()):
        if pid in used:
            continue
        if is_gift_card(pid):
            skipped_gift.append(pid)
            continue
        sources = existing_sources(pid, audience)
        if not sources:
            # Sem fonte Drive e sem raster local — reportar (não inventar arte).
            kept.append(pid)
            continue
        # Já há WebP oficial/local: não re-comprimir só por estar em missing.
        webp = (PRODUCTS / "male" if audience == "masculino" else PRODUCTS) / f"{pid}.webp"
        if webp.is_file() and webp.stat().st_size > 1000:
            kept.append(pid)
            print(f"missing-official keep-local {pid}", flush=True)
            continue
        source = max(sources, key=lambda path: path.stat().st_size)
        dest = source.with_suffix(".webp")
        to_webp(source.read_bytes(), dest)
        for old in sources:
            if old != dest:
                old.unlink()
        kept.append(pid)
        print(f"kept-old {pid}", flush=True)

    report = {
        "replaced": replaced,
        "missing_official": kept,
        "skipped_gift_cards": sorted(set(skipped_gift)),
        "drive_files_without_product": unmatched_files,
    }
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        f"replaced {len(replaced)} missing {len(kept)} gifts {len(set(skipped_gift))} extra {len(unmatched_files)}",
        flush=True,
    )


if __name__ == "__main__":
    main()
