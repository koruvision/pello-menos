"""Generate missing Pello Menos product images via Gemini (one unique file per SKU)."""
from __future__ import annotations

import os
import re
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
PRODUCTS = OUT / "products"
MALE = PRODUCTS / "male"

API_KEY = os.environ.get("VERTEX_AI_KEY") or os.environ.get("GOOGLE_API_KEY") or ""
MODEL = os.environ.get("GEMINI_IMAGE_MODEL", "gemini-2.5-flash-image")

STYLE = (
    "Photoreal square 1:1 beauty-clinic catalog photo for the Brazilian brand Pello Menos. "
    "Premium editorial, cream/champagne studio, soft cinematic lighting, extremely smooth skin. "
    "Overlay: elegant thin dashed line in deep plum #700053 with a subtle gold #E8B86D accent, "
    "marking ONLY the treatment area. "
    "Do NOT add readable text, watermarks, prices, or fake logos. "
    "No nudity. Tasteful commercial beauty photography only. Keep underwear or clothing on. "
)

CANONICAL_MALE = {
    "peito-cera-masc": MALE / "peito.jpg",
    "abdomen-cera-masc": MALE / "abdomen.jpg",
    "axila-cera-masc": MALE / "axilas.jpg",
    "antebraco-cera-masc": MALE / "antebraco.jpg",
    "bracos-cera-masc": MALE / "bracos.jpg",
    "costas-cera-masc": MALE / "costas.jpg",
    "perna-cera-masc": MALE / "pernas.jpg",
    "virilha-cera-masc": MALE / "virilha.jpg",
    "queixo-cera-masc": MALE / "barba.jpg",
    "pescoco-laser-masc": MALE / "pescoco.jpg",
}


def catalog_jobs() -> list[dict]:
    text = (ROOT / "src" / "lib" / "data.ts").read_text(encoding="utf-8")
    block = text.split("const catalogItems")[1].split("function defaultDescription")[0]
    items = re.findall(
        r'id: "([^"]+)"[\s\S]*?catalogImage\("([^"]+)"(?:, "(masculino)")?\)',
        block,
    )
    jobs = []
    for pid, img_id, aud in items:
        dest = CANONICAL_MALE.get(img_id)
        if dest is None:
            dest = (MALE if aud == "masculino" else PRODUCTS) / f"{img_id}.png"
        method = "laser" if "laser" in pid else "esfoliacao" if "esfolia" in pid else "linha" if "linha" in pid else "plano" if "plano" in pid else "cera"
        gender = "Brazilian man" if aud == "masculino" else "Brazilian woman"
        extra = {
            "laser": " LASER mood: faint cool lilac glow on the marked zone.",
            "esfoliacao": " Body-scrub scene with a warm gold glow, no wax overlay.",
            "linha": " Threading with a cotton string, not wax.",
            "plano": " Luxury still-life, no person required if it is a membership card.",
            "cera": " Waxing treatment zone.",
        }[method]
        jobs.append(
            {
                "id": img_id,
                "dest": dest,
                "prompt": STYLE + f" Subject: {gender}. Unique crop for SKU {pid}." + extra,
                "ratio": "1:1",
            }
        )
    return jobs


def image_part(path: Path) -> types.Part:
    im = Image.open(path).convert("RGB")
    tmp = ROOT / "_tmp_upload.jpg"
    im.save(tmp, "JPEG", quality=92)
    data = tmp.read_bytes()
    tmp.unlink(missing_ok=True)
    return types.Part.from_bytes(data=data, mime_type="image/jpeg")


def nearest_ref(job: dict) -> Path | None:
    dest: Path = job["dest"]
    if dest.exists() and dest.stat().st_size > 8_000:
        return dest
    refs = sorted(REF.glob("*")) if REF.exists() else []
    return refs[0] if refs else (LOGO if LOGO.exists() else None)


def generate_one(client: genai.Client, job: dict) -> Path:
    dest: Path = job["dest"]
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 20_000:
        print("skip", dest.name, flush=True)
        return dest

    contents = [job["prompt"]]
    if LOGO.exists():
        contents.insert(0, image_part(LOGO))
        contents[-1] = (
            job["prompt"]
            + " Use the first image only as brand color/mood reference (plum + gold)."
        )
    ref = nearest_ref(job)
    if ref and ref != LOGO:
        contents.insert(-1, image_part(ref))

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
    force = "--force" in sys.argv
    client = genai.Client(api_key=API_KEY)
    failed = []
    for job in catalog_jobs():
        if not force and job["dest"].exists():
            print("skip", job["id"], flush=True)
            continue
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
