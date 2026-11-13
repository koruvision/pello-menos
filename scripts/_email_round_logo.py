# -*- coding: utf-8 -*-
"""Logo redonda com borda dourada para e-mails Woo + option na loja (ou oficialteste).

Fonte: wordmark transparente `media/brand/logo-footer.png` (fundo preto removido).
Saída: PNG circular, fill roxo da marca, anel dourado #FFBB3A, filete branco; retina 2x.
"""
from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import urllib.error
import urllib.request
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "wordpress-loja" / "pm-home" / "media" / "brand" / "logo-footer.png"
OUT = ROOT / "wordpress-loja" / "pm-home" / "media" / "brand" / "pello-menos-email-logo-round.png"

GOLD = (255, 187, 58, 255)  # #FFBB3A
WHITE = (255, 255, 255, 255)
FILL = (112, 0, 83, 255)  # #700053 — legível sob o wordmark branco
CANVAS = 320
DIAMETER = 288
BORDER = 6
INNER_RING = 2
EMAIL_WIDTH = "180"
LOGO_PAD = 28  # folga dentro do filete


def env_path_for(prefix: str) -> Path:
    name = "loja.env" if prefix == "PM_LOJA" else "oficialteste.env"
    return ROOT / "projeto-migracao" / ".secrets" / name


def env(prefix: str) -> dict:
    values = {}
    for line in env_path_for(prefix).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        values[k.strip()] = v.strip()
    return values


def call(prefix: str, method: str, path: str, payload=None, raw=None, content_type=None, headers_extra=None):
    cfg = env(prefix)
    base = cfg[f"{prefix}_URL"].rstrip("/")
    token = base64.b64encode(
        f"{cfg[f'{prefix}_USER']}:{cfg[f'{prefix}_APP_PASSWORD']}".encode()
    ).decode()
    data = raw if raw is not None else (None if payload is None else json.dumps(payload).encode())
    headers = {
        "Authorization": "Basic " + token,
        "Accept": "application/json",
        "User-Agent": "pm-email-round/2.0",
    }
    if headers_extra:
        headers.update(headers_extra)
    if content_type:
        headers["Content-Type"] = content_type
    elif payload is not None:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(base + path, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            body = r.read().decode("utf-8", "replace")
            return r.status, json.loads(body) if body.strip()[:1] in "{[" else body
    except urllib.error.HTTPError as e:
        raw_body = e.read().decode("utf-8", "replace")
        try:
            return e.code, json.loads(raw_body)
        except Exception:
            return e.code, raw_body[:800]


def _disc(size: int, color, scale: int = 4) -> Image.Image:
    big = Image.new("RGBA", (size * scale, size * scale), (0, 0, 0, 0))
    ImageDraw.Draw(big).ellipse((0, 0, size * scale - 1, size * scale - 1), fill=color)
    return big.resize((size, size), Image.Resampling.LANCZOS)


def make_round_logo() -> Path:
    if not SRC.is_file():
        raise SystemExit(f"missing source {SRC}")
    src = Image.open(SRC).convert("RGBA")
    # Tight crop to opaque content
    alpha = src.split()[-1]
    bbox = alpha.getbbox()
    if bbox:
        src = src.crop(bbox)

    inner = DIAMETER - (BORDER + INNER_RING) * 2
    fit = inner - LOGO_PAD * 2
    scale = min(fit / src.width, fit / src.height)
    nw, nh = max(1, int(round(src.width * scale))), max(1, int(round(src.height * scale)))
    src = src.resize((nw, nh), Image.Resampling.LANCZOS)

    canvas = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
    cx = cy = CANVAS // 2

    shadow = _disc(DIAMETER, (60, 0, 30, 110))
    shadow_layer = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
    shadow_layer.paste(shadow, (cx - DIAMETER // 2, cy - DIAMETER // 2 + 6), shadow)
    shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(8))
    canvas = Image.alpha_composite(canvas, shadow_layer)

    gold = _disc(DIAMETER, GOLD)
    canvas.paste(gold, (cx - DIAMETER // 2, cy - DIAMETER // 2), gold)
    white_d = DIAMETER - BORDER * 2
    white = _disc(white_d, WHITE)
    canvas.paste(white, (cx - white_d // 2, cy - white_d // 2), white)
    fill = _disc(inner, FILL)
    canvas.paste(fill, (cx - inner // 2, cy - inner // 2), fill)
    canvas.paste(src, (cx - nw // 2, cy - nh // 2), src)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(OUT, "PNG", optimize=True)
    print(
        "wrote",
        OUT,
        OUT.stat().st_size,
        "canvas",
        CANVAS,
        "diameter",
        DIAMETER,
        "border",
        BORDER,
    )
    return OUT


def upload(prefix: str, path: Path) -> str:
    blob = path.read_bytes()
    filename = path.name
    ctype = mimetypes.guess_type(filename)[0] or "image/png"
    st, media = call(
        prefix,
        "POST",
        "/wp-json/wp/v2/media",
        raw=blob,
        content_type=ctype,
        headers_extra={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
    print("upload", st)
    if st not in (200, 201) or not isinstance(media, dict):
        raise SystemExit(f"upload failed {st} {media}")
    url = media.get("source_url")
    print("url", url, "id", media.get("id"))
    return url


def apply_option(prefix: str, logo_url: str) -> None:
    name = "pm-email-logo-once"
    code = f"""// {name} round
$dir = wp_upload_dir();
$dump = $dir['basedir'] . '/pm-home/email-logo-dump.json';
update_option('woocommerce_email_header_image', '{logo_url}');
update_option('woocommerce_email_header_image_width', '{EMAIL_WIDTH}');
update_option('woocommerce_email_header_alignment', 'center');
update_option('woocommerce_email_background_color', '#700053');
update_option('woocommerce_email_body_background_color', '#FFFFFF');
@file_put_contents($dump, wp_json_encode(array(
  'header' => get_option('woocommerce_email_header_image'),
  'width' => get_option('woocommerce_email_header_image_width'),
  'align' => get_option('woocommerce_email_header_alignment'),
  'bg' => get_option('woocommerce_email_background_color'),
  'body_bg' => get_option('woocommerce_email_body_background_color'),
  'base' => get_option('woocommerce_email_base_color'),
  'footer_text' => get_option('woocommerce_email_footer_text'),
  'ts' => time(),
)));
"""
    st, rows = call(prefix, "GET", "/wp-json/code-snippets/v1/snippets")
    sid = None
    if isinstance(rows, list):
        for row in rows:
            if row.get("name") == name:
                sid = row.get("id")
    payload = {"name": name, "code": code, "scope": "global", "active": True}
    if sid is None:
        st, saved = call(prefix, "POST", "/wp-json/code-snippets/v1/snippets", payload)
    else:
        st, saved = call(prefix, "PUT", f"/wp-json/code-snippets/v1/snippets/{sid}", payload)
    print("snippet on", st, saved.get("id") if isinstance(saved, dict) else saved)
    sid = saved.get("id") if isinstance(saved, dict) else sid
    call(prefix, "GET", "/wp-json/wp/v2/users/me")
    for sid_set, value in (
        ("woocommerce_email_header_image_width", EMAIL_WIDTH),
        ("woocommerce_email_header_alignment", "center"),
        ("woocommerce_email_background_color", "#700053"),
        ("woocommerce_email_body_background_color", "#FFFFFF"),
    ):
        st2, _ = call(prefix, "PUT", f"/wp-json/wc/v3/settings/email/{sid_set}", {"value": value})
        print("PUT", sid_set, st2)
    call(
        prefix,
        "PUT",
        f"/wp-json/code-snippets/v1/snippets/{sid}",
        {"name": name, "code": code, "scope": "global", "active": False},
    )
    cfg = env(prefix)
    dump_url = cfg[f"{prefix}_URL"].rstrip("/") + "/wp-content/uploads/pm-home/email-logo-dump.json"
    req = urllib.request.Request(dump_url + f"?t={OUT.stat().st_mtime}", headers={"User-Agent": "pm"})
    with urllib.request.urlopen(req, timeout=60) as r:
        dump = json.loads(r.read().decode())
    print("dump", dump)
    if dump.get("header") != logo_url:
        raise SystemExit("header not updated")
    if dump.get("align") != "center":
        raise SystemExit("align not center")
    print("DONE")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--prefix",
        default="PM_LOJA",
        choices=("PM_LOJA", "PM_OFICIALTESTE"),
        help="Destino das credenciais (.secrets)",
    )
    parser.add_argument("--make-only", action="store_true", help="Só gera o PNG local")
    args = parser.parse_args()
    make_round_logo()
    if args.make_only:
        return
    url = upload(args.prefix, OUT)
    apply_option(args.prefix, url)


if __name__ == "__main__":
    main()
