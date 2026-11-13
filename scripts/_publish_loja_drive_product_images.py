# -*- coding: utf-8 -*-
"""Espelha WebP do Drive (public/) no pm-home, atualiza ?v=hash e publica na loja."""
from __future__ import annotations

import base64
import hashlib
import io
import json
import re
import shutil
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV = ROOT / "projeto-migracao" / ".secrets" / "loja.env"
PUBLIC = ROOT / "public" / "images" / "products"
PM = ROOT / "wordpress-loja" / "pm-home"
MEDIA = PM / "media" / "images" / "products"
CLONE = "https://pellomenos.companygenesis.com.br/wp-content/uploads/pm-home"


def cfg():
    e = {}
    for line in ENV.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            e[k.strip().lstrip("\ufeff")] = v.strip()
    return {
        "url": e["PM_LOJA_URL"].rstrip("/"),
        "user": e["PM_LOJA_USER"],
        "password": e["PM_LOJA_APP_PASSWORD"],
    }


def call(c, method, path, raw=None, content_type=None, payload=None):
    tok = base64.b64encode(f"{c['user']}:{c['password']}".encode()).decode()
    headers = {
        "Authorization": "Basic " + tok,
        "User-Agent": "pm-drive-images",
        "Accept": "application/json",
    }
    data = raw
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    elif raw is not None:
        headers["Content-Type"] = content_type or "application/octet-stream"
    req = urllib.request.Request(c["url"] + path, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=900) as r:
            body = r.read().decode("utf-8", "replace")
            try:
                parsed = json.loads(body) if body else None
            except Exception:
                parsed = body
            return r.status, parsed
    except urllib.error.HTTPError as err:
        body = err.read().decode("utf-8", "replace")
        try:
            parsed = json.loads(body)
        except Exception:
            parsed = body[:500]
        return err.code, parsed


def short_hash(path: Path) -> str:
    return hashlib.md5(path.read_bytes()).hexdigest()[:8]


def mirror() -> list[Path]:
    MEDIA.mkdir(parents=True, exist_ok=True)
    (MEDIA / "male").mkdir(parents=True, exist_ok=True)
    copied: list[Path] = []
    for src in list(PUBLIC.glob("*.webp")) + list((PUBLIC / "male").glob("*.webp")):
        rel = src.relative_to(PUBLIC)
        dest = MEDIA / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
        copied.append(dest)
    print("mirrored", len(copied), "webp ->", MEDIA.relative_to(ROOT))
    return copied


def hash_map() -> dict[str, str]:
    """filename or male/filename -> md5[:8]"""
    out: dict[str, str] = {}
    for path in list(MEDIA.glob("*.webp")) + list((MEDIA / "male").glob("*.webp")):
        if path.parent.name == "male":
            key = f"male/{path.name}"
        else:
            key = path.name
        out[key] = short_hash(path)
    return out


def bump_versions(hashes: dict[str, str]) -> int:
    """Rewrite ?v= for product images in html/json/js under pm-home."""
    changed = 0
    pat = re.compile(
        r"(media/images/products/(?:male/)?[A-Za-z0-9._\-]+\.webp)(?:\?v=[a-f0-9]{8})?",
        re.I,
    )

    def repl(match: re.Match) -> str:
        path = match.group(1).replace("\\", "/")
        # media/images/products/foo.webp -> foo.webp
        # media/images/products/male/foo.webp -> male/foo.webp
        rel = path.split("media/images/products/", 1)[-1]
        h = hashes.get(rel)
        if not h:
            return match.group(0)
        return f"{path}?v={h}"

    for path in PM.rglob("*"):
        if path.suffix.lower() not in {".html", ".json", ".js"}:
            continue
        if "node_modules" in path.parts:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if "media/images/products/" not in text and "/images/products/" not in text:
            continue
        # also rewrite bare /images/products paths used in some JSON
        new = pat.sub(repl, text)
        new = re.sub(
            r"(/images/products/(?:male/)?[A-Za-z0-9._\-]+\.webp)(?:\?v=[a-f0-9]{8})?",
            lambda m: (
                f"{m.group(1)}?v={hashes.get(m.group(1).split('/images/products/', 1)[-1], '')}"
                if hashes.get(m.group(1).split("/images/products/", 1)[-1])
                else m.group(0)
            ),
            new,
        )
        if new != text:
            path.write_text(new, encoding="utf-8")
            changed += 1
            print("bumped", path.relative_to(PM))
    print("files bumped", changed)
    return changed


def publish(c, copied: list[Path]) -> None:
    dest_base = c["url"] + "/wp-content/uploads/pm-home"
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        # all product webps
        for path in copied:
            rel = path.relative_to(PM).as_posix()
            z.writestr(rel, path.read_bytes())
        # html/json that may carry new ?v=
        for path in PM.rglob("*"):
            if path.suffix.lower() not in {".html", ".json"}:
                continue
            if path.name in {"pages.json", "routes.json", "woo-slugs.json", "woo-bridge.json"}:
                rel = path.relative_to(PM).as_posix()
                raw = path.read_bytes()
                z.writestr(rel, raw)
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            if "media/images/products/" not in text and "/images/products/" not in text:
                continue
            rel = path.relative_to(PM).as_posix()
            if path.suffix.lower() == ".html":
                text = text.replace(CLONE, dest_base)
            z.writestr(rel, text.encode("utf-8"))
        print("zip entries", len(z.namelist()))
    st, body = call(
        c,
        "POST",
        "/wp-json/pm-home/v1/bundle",
        raw=buf.getvalue(),
        content_type="application/zip",
    )
    print("bundle", st, body if isinstance(body, dict) else str(body)[:300])
    if st != 200:
        raise SystemExit(1)


def verify(c, hashes: dict[str, str]) -> None:
    samples = [
        "axila-cera.webp",
        "axila-laser.webp",
        "male/axila-cera-masc.webp",
        "plano-gold.webp",
        "body-splash-livre.webp",
    ]
    for name in samples:
        h = hashes.get(name)
        if not h:
            print("skip verify missing", name)
            continue
        url = f"{c['url']}/wp-content/uploads/pm-home/media/images/products/{name}?v={h}"
        req = urllib.request.Request(
            url, headers={"User-Agent": "pm", "Cache-Control": "no-cache"}
        )
        with urllib.request.urlopen(req, timeout=60) as r:
            data = r.read(32)
            print(name, r.status, len(data), "webp" if data[:4] == b"RIFF" else data[:12])


def main() -> None:
    c = cfg()
    assert "loja.pellomenos.com.br" in c["url"]
    copied = mirror()
    hashes = hash_map()
    bump_versions(hashes)
    publish(c, copied)
    verify(c, hashes)
    print("LOJA_DRIVE_IMAGES_OK", len(copied))


if __name__ == "__main__":
    main()
