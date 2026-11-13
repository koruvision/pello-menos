"""Build product_image_batch.json with GenerateImage descriptions."""
from __future__ import annotations

import json
from pathlib import Path

REF = r"C:\Users\GC1\.cursor\projects\c-Users-GC1-Desktop-pello-menos\assets\c__Users_GC1_AppData_Roaming_Cursor_User_workspaceStorage_5fbd0f4a155bce6742dfd1809ecf2a22_images_image-5dd49f35-80a2-4c81-8953-e120dabca8f5.jpg"
ASSETS = r"C:\Users\GC1\.cursor\projects\c-Users-GC1-Desktop-pello-menos\assets"
OUT = r"C:\Users\GC1\Desktop\pello-menos\public\images\products"

STYLES = {
    "linha": "Soft lavender purple gradient background. Purple dashed oval outline on skin marking the treatment zone.",
    "laser": "Vibrant pink magenta gradient background. Pink dashed oval outline on skin marking the treatment zone.",
    "esfoliacao": "Warm golden yellow champagne gradient background. Gold dashed oval outline on skin marking the treatment zone.",
    "cera": "Soft light blue gradient background. Blue dashed oval outline on skin marking the treatment zone.",
}

SCENES: dict[str, str] = {
    "buco-linha": "Close-up of adult woman's face, white top, purple dashed oval on upper lip area.",
    "queixo-linha": "Close-up adult woman chin and lower face, white clothing, oval on chin.",
    "faixa-linha": "Adult woman lower abdomen hip level, white crop top and white athletic shorts, oval on horizontal bikini-line strip on lower belly.",
    "buco-laser": "Close-up adult woman face, white top, pink oval on upper lip area.",
    "axilas-laser": "Adult woman white tank top, arm raised behind head, smooth underarm, pink oval on underarm like reference.",
    "antebraco-laser": "Adult woman forearm extended, white tank top, pink oval on forearm skin.",
    "bracos-laser": "Adult woman both arms visible, white tank top, pink ovals on upper arms.",
    "costas-laser": "Adult woman back view, white sports bra, pink oval on upper back between shoulder blades.",
    "perna-laser": "Adult woman full leg side view, white athletic shorts, pink oval along full leg.",
    "meia-perna-laser": "Adult woman lower leg and calf, white shorts, pink oval on shin and calf region.",
    "nadegas-laser": "Adult woman rear view clinical, white athletic shorts, pink oval on full buttocks area modest framing.",
    "meia-nadega-laser": "Adult woman rear three-quarter view, white shorts, pink oval on one buttock cheek.",
    "intergluteos-laser": "Adult woman rear clinical modest, white athletic shorts, pink oval on intergluteal cleft area.",
    "virilha-laser": "Adult woman hip level front three-quarter, white athletic underwear and crop top, pink oval on bikini zone modest clinical.",
    "nariz-laser": "Close-up adult woman nose and mid face, white top, pink oval on nose bridge and tip.",
    "orelhas-laser": "Close-up adult woman ear and jaw, hair tied back, white top, pink oval around ear.",
    "queixo-laser": "Close-up adult woman chin, white top, pink oval on chin.",
    "pescoco-laser": "Adult woman neck and collarbone, white tank top, pink oval on front neck.",
    "rosto-inteiro-laser": "Adult woman full face portrait, white top, pink oval framing entire face skin area.",
    "psd-p-laser": "Adult woman bikini area clinical modest, white athletic underwear, pink small oval on compact bikini laser zone.",
    "psd-m-laser": "Adult woman bikini area clinical modest, white athletic underwear, pink medium oval on standard bikini laser zone.",
    "psd-g-laser": "Adult woman bikini area clinical modest, white athletic underwear, pink large oval on extended bikini laser zone.",
    "esfoliacao-faixa": "Adult woman lower abdomen, white crop and shorts, gold oval on bikini-line strip for body scrub zone.",
    "esfoliacao-meio-braco": "Adult woman upper arm half length, white tank, gold oval on mid upper arm.",
    "esfoliacao-braco": "Adult woman full arm, white tank, gold oval along arm for scrub.",
    "esfoliacao-meia-perna": "Adult woman lower leg, white shorts, gold oval on calf and lower thigh.",
    "esfoliacao-abdomen": "Adult woman abdomen, white crop top, gold oval on stomach skin.",
    "esfoliacao-axilas": "Adult woman arm raised, white tank, gold oval on underarm.",
    "esfoliacao-costas": "Adult woman back, white sports bra, gold oval on back skin.",
    "esfoliacao-coxa": "Adult woman thigh side view, white shorts, gold oval on thigh.",
    "esfoliacao-nadegas": "Adult woman rear modest white shorts, gold oval on buttocks scrub zone.",
    "esfoliacao-perna": "Adult woman full leg, white shorts, gold oval along leg.",
    "esfoliacao-virilha": "Adult woman hip level modest white underwear, gold oval on bikini zone clinical.",
    "sobrancelha-realce-cera": "Close-up adult woman eyebrows and brow bone, white top, blue oval highlighting brow and tint zone.",
    "sobrancelha-henna-simples": "Close-up adult woman eyebrow, white top, blue oval on single brow henna area.",
    "design-sobrancelha-realce": "Close-up adult woman both eyebrows shaped, white top, blue ovals on brows and design zone.",
    "sobrancelha-henna": "Close-up adult woman eyebrows, white top, blue ovals on brow henna zones.",
    "realce": "Close-up adult woman eyebrow tint realce, white top, blue oval on brow area.",
    "henna": "Close-up adult woman eyebrow henna, white top, blue oval on brow.",
    "labios-genitais-cera": "Clinical spa framing adult woman lower bikini modest white underwear, blue oval on outer labia wax zone, tasteful medical aesthetic.",
    "virilha-comum-faixa-cera": "Adult woman white underwear, blue oval on standard bikini line strip wax zone.",
    "virilha-cavada-cera": "Adult woman white underwear modest, blue oval on deep bikini wax zone clinical.",
    "virilha-cavada-faixa-cera": "Adult woman white underwear, blue oval on deep bikini plus strip zone.",
    "virilha-modelada-cera": "Adult woman white underwear, blue oval on sculpted bikini wax shape zone.",
    "intergluteos-cera": "Adult woman rear modest white shorts, blue oval on intergluteal wax zone.",
    "nariz-cera": "Close-up adult woman nose, white top, blue oval on nose wax zone.",
}

TAIL = (
    "Professional e-commerce beauty clinic campaign photo matching reference moodboard layout. "
    "Soft halo studio lighting. White clothing only. Adult model. No text. No logos. Square 1:1."
)


def style_key(pid: str) -> str:
    if pid.startswith("esfoliacao"):
        return "esfoliacao"
    if pid.endswith("-linha") or "-linha" in pid:
        return "linha"
    if "laser" in pid:
        return "laser"
    return "cera"


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    out_dir = root / "public" / "images" / "products"
    jobs = []
    for pid, scene in SCENES.items():
        if not (out_dir / f"{pid}.png").exists():
            continue
        sk = style_key(pid)
        desc = f"{scene} {STYLES[sk]} {TAIL}"
        jobs.append(
            {
                "id": pid,
                "filename": f"gen-{pid}.jpg",
                "description": desc,
            }
        )
    batch = {
        "reference": REF,
        "assetsDir": ASSETS,
        "outDir": str(out_dir),
        "jobs": jobs,
    }
    path = root / "scripts" / "product_image_batch.json"
    path.write_text(json.dumps(batch, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {len(jobs)} jobs to {path}")


if __name__ == "__main__":
    main()
