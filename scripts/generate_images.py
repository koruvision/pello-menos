"""Generate Pello Menos product/hero/category images via Vertex express Gemini."""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path

from google import genai
from google.genai import types
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "public" / "images"
REF = ROOT / "public" / "images" / "ref"
LOGO = ROOT / "public" / "brand" / "logo.png"

API_KEY = os.environ.get("VERTEX_AI_KEY") or os.environ.get("GOOGLE_API_KEY") or ""
MODEL = os.environ.get("GEMINI_IMAGE_MODEL", "gemini-2.5-flash-image")

STYLE = (
    "Recreate this beauty-service product photo in a MORE MODERN editorial style "
    "for the Brazilian brand Pello Menos (depilação). Keep the same body area and "
    "the same idea of a treatment-zone overlay, but upgrade the look: "
    "premium clinic photography, soft cinematic lighting, cream/champagne studio "
    "background with a faint warm glow, extremely smooth skin, high-end 2026 beauty campaign. "
    "Overlay: elegant thin dashed line in deep plum #700053 with a subtle gold #E8B86D accent, "
    "marking ONLY the treatment area. "
    "Do NOT add readable text, watermarks, prices, or fake logos. "
    "No nudity. Tasteful commercial beauty photography only. "
    "Square composition, 1:1, catalog crop."
)


JOBS = [
    {
        "id": "buco-cera",
        "ref": "buco-cera.webp",
        "folder": "products",
        "ratio": "1:1",
        "prompt": STYLE + " Subject: woman's face, upper-lip (buço) and chin treatment zone.",
    },
    {
        "id": "axila-cera",
        "ref": "axila-cera.webp",
        "folder": "products",
        "ratio": "1:1",
        "prompt": STYLE + " Subject: woman in a white camisole, arm raised, underarm (axila) treatment zone.",
    },
    {
        "id": "virilha-cera",
        "ref": "virilha-cera.webp",
        "folder": "products",
        "ratio": "1:1",
        "prompt": STYLE
        + " Subject: woman in white underwear and white top, bikini/groin treatment zone marked with a tasteful dashed overlay. Keep underwear on. No explicit nudity.",
    },
    {
        "id": "perna-cera",
        "ref": "perna-cera.webp",
        "folder": "products",
        "ratio": "1:1",
        "prompt": STYLE + " Subject: woman's full legs from waist to feet, white underwear, full-leg treatment overlay.",
    },
    {
        "id": "axilas-laser",
        "ref": "axila-cera.webp",
        "folder": "products",
        "ratio": "1:1",
        "prompt": STYLE
        + " Same underarm scene, but this is LASER hair removal: add a subtle cool-lilac light glow on the marked zone, still tasteful, not sci-fi.",
    },
    {
        "id": "buco-laser",
        "ref": "buco-cera.webp",
        "folder": "products",
        "ratio": "1:1",
        "prompt": STYLE
        + " Same face/upper-lip scene, LASER version: faint lilac glow on the marked lip and chin zones.",
    },
    {
        "id": "virilha-laser",
        "ref": "virilha-cera.webp",
        "folder": "products",
        "ratio": "1:1",
        "prompt": STYLE
        + " Same bikini-area scene with underwear on, LASER version: faint lilac glow on the marked zone. No nudity.",
    },
    {
        "id": "perna-laser",
        "ref": "perna-cera.webp",
        "folder": "products",
        "ratio": "1:1",
        "prompt": STYLE
        + " Same full-legs scene, LASER version: faint lilac glow along the marked legs.",
    },
    {
        "id": "hero-laser",
        "ref": "axila-cera.webp",
        "folder": "hero",
        "ratio": "16:9",
        "prompt": (
            "Cinematic wide 16:9 beauty campaign still for Pello Menos laser hair removal. "
            "Modern clinic, warm cream and deep plum lighting, a confident Brazilian woman, "
            "soft gold highlights. No readable text, no fake logo. Premium 2026 editorial."
        ),
    },
    {
        "id": "hero-cera",
        "ref": "perna-cera.webp",
        "folder": "hero",
        "ratio": "16:9",
        "prompt": (
            "Cinematic wide 16:9 campaign still for Pello Menos waxing. Smooth legs, "
            "cream studio, plum and gold color grade, boutique spa mood. No text, no fake logo."
        ),
    },
    {
        "id": "hero-verao",
        "ref": "perna-cera.webp",
        "folder": "hero",
        "ratio": "16:9",
        "prompt": (
            "Cinematic wide 16:9 summer campaign for Pello Menos. Sunlit skin, linen, "
            "gold hour mixed with plum shadows, ready-for-summer feeling. No text, no fake logo."
        ),
    },
    {
        "id": "cat-axilas",
        "ref": "axila-cera.webp",
        "folder": "categories",
        "ratio": "1:1",
        "prompt": STYLE + " Tight square crop of the underarm treatment, circular-friendly composition.",
    },
    {
        "id": "cat-virilha",
        "ref": "virilha-cera.webp",
        "folder": "categories",
        "ratio": "1:1",
        "prompt": STYLE + " Tight square crop of the bikini treatment overlay, underwear on, no nudity.",
    },
    {
        "id": "cat-pernas",
        "ref": "perna-cera.webp",
        "folder": "categories",
        "ratio": "1:1",
        "prompt": STYLE + " Tight square crop focused on smooth legs.",
    },
    {
        "id": "cat-rosto",
        "ref": "buco-cera.webp",
        "folder": "categories",
        "ratio": "1:1",
        "prompt": STYLE + " Tight square beauty portrait for facial waxing category.",
    },
    {
        "id": "promo-semana",
        "ref": "axila-cera.webp",
        "folder": "hero",
        "ratio": "16:9",
        "prompt": (
            "Wide 16:9 boutique spa interior, plum velvet and gold details, cream marble, "
            "Pello Menos beauty week mood. Empty of text. Photoreal, premium."
        ),
    },
    {
        "id": "promo-laser",
        "ref": "axila-cera.webp",
        "folder": "hero",
        "ratio": "16:9",
        "prompt": (
            "Wide 16:9 close-up of a modern laser hair-removal handpiece in a cream clinic, "
            "soft plum ambient light, gold reflections. No readable text."
        ),
    },
    {
        "id": "square-kits",
        "ref": "buco-cera.webp",
        "folder": "hero",
        "ratio": "1:1",
        "prompt": (
            "Square still life of premium home-care beauty products (serum, cream) on cream linen, "
            "plum and gold packaging, no readable logos or fake brand names."
        ),
    },
    {
        "id": "square-verao",
        "ref": "perna-cera.webp",
        "folder": "hero",
        "ratio": "1:1",
        "prompt": (
            "Square summer beauty photo: smooth sunlit legs, linen, gold hour, plum shadow. No text."
        ),
    },
    {
        "id": "square-presente",
        "ref": "axila-cera.webp",
        "folder": "hero",
        "ratio": "1:1",
        "prompt": (
            "Square gift-card still life: plum envelope and gold ribbon on black and cream, "
            "luxury spa voucher mood, no readable text."
        ),
    },
]


def load_png_bytes(path: Path) -> bytes:
    im = Image.open(path).convert("RGBA")
    tmp = path.with_suffix(".gen.png")
    if tmp != path:
        im.save(tmp)
        data = tmp.read_bytes()
        if str(tmp).endswith(".gen.png"):
            tmp.unlink(missing_ok=True)
            buf_path = ROOT / "tmp_ref.png"
            im.save(buf_path)
            data = buf_path.read_bytes()
            buf_path.unlink(missing_ok=True)
            return data
    return path.read_bytes()


def image_part(path: Path) -> types.Part:
    im = Image.open(path).convert("RGB")
    tmp = ROOT / "_tmp_upload.jpg"
    im.save(tmp, "JPEG", quality=92)
    data = tmp.read_bytes()
    tmp.unlink(missing_ok=True)
    return types.Part.from_bytes(data=data, mime_type="image/jpeg")


def generate_one(client: genai.Client, job: dict) -> Path:
    dest_dir = OUT / job["folder"]
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / f"{job['id']}.png"
    if dest.exists() and dest.stat().st_size > 20_000:
        print("skip", dest.name, flush=True)
        return dest

    ref = REF / job["ref"]
    contents = [
        image_part(LOGO),
        image_part(ref),
        job["prompt"]
        + " Use the first image only as brand color/mood reference (plum + gold). "
        "Use the second image as the pose/composition reference to modernize.",
    ]
    config = types.GenerateContentConfig(
        response_modalities=["IMAGE"],
        image_config=types.ImageConfig(aspect_ratio=job["ratio"]),
        safety_settings=[
            types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="BLOCK_ONLY_HIGH"),
            types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="BLOCK_ONLY_HIGH"),
            types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="BLOCK_ONLY_HIGH"),
            types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="BLOCK_ONLY_HIGH"),
        ],
    )
    print("gen", job["id"], flush=True)
    last_err = None
    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model=MODEL,
                contents=contents,
                config=config,
            )
            parts = []
            if response.candidates:
                parts = response.candidates[0].content.parts or []
            for part in parts:
                inline = getattr(part, "inline_data", None)
                if inline and inline.data:
                    dest.write_bytes(inline.data)
                    print("ok", dest.name, dest.stat().st_size, flush=True)
                    return dest
            last_err = RuntimeError(f"no image in response: {getattr(response, 'text', None)}")
        except Exception as exc:
            last_err = exc
            print("retry", job["id"], type(exc).__name__, str(exc)[:220], flush=True)
            time.sleep(4 * (attempt + 1))
    raise RuntimeError(f"{job['id']} failed: {last_err}")


def main() -> None:
    if not API_KEY:
        print("Missing VERTEX_AI_KEY", file=sys.stderr)
        sys.exit(1)
    client = genai.Client(api_key=API_KEY)
    failed = []
    for job in JOBS:
        try:
            generate_one(client, job)
        except Exception as exc:
            print("FAIL", job["id"], str(exc)[:300], flush=True)
            failed.append(job["id"])
    print("DONE failed", failed, flush=True)
    if failed:
        sys.exit(2)


if __name__ == "__main__":
    main()
