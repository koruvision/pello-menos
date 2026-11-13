# -*- coding: utf-8 -*-
"""Specs for regenerating home product images in moodboard style."""
from __future__ import annotations

# method -> (bg description, dashed oval color)
METHOD_LOOK = {
    "cera": (
        "warm golden-yellow honey gradient background with soft circular halo glow behind the subject",
        "bright gold/yellow",
    ),
    "linha": (
        "soft lavender light-purple gradient background with soft circular halo glow behind the subject",
        "solid purple",
    ),
    "laser": (
        "pink magenta gradient background with soft circular halo glow behind the subject",
        "bright pink/magenta",
    ),
    "esfoliacao": (
        "warm golden-yellow honey gradient background with soft circular halo glow behind the subject",
        "bright gold/yellow",
    ),
    "cera_masc": (
        "light sky-blue gradient background with soft circular halo glow behind the subject",
        "bright blue",
    ),
    "laser_masc": (
        "dark periwinkle indigo blue-purple gradient background with soft circular halo glow behind the subject",
        "dark indigo blue",
    ),
    "esfoliacao_masc": (
        "warm golden-yellow honey gradient background with soft circular halo glow behind the subject",
        "bright gold/yellow",
    ),
}

# product id base (without -masc) -> body region for dashed oval
REGION = {
    "abdomen-cera": "abdomen / belly area centered",
    "axila-cera": "underarm / armpit with arm raised behind head",
    "axilas-laser": "underarm / armpit with arm raised",
    "antebraco-cera": "forearm from elbow to wrist",
    "antebraco-laser": "forearm from elbow to wrist",
    "bracos-cera": "full upper arm",
    "bracos-laser": "full upper arm",
    "buco-cera": "upper lip mustache area close-up",
    "buco-linha": "upper lip mustache area close-up for threading",
    "buco-laser": "upper lip mustache area",
    "costas-cera": "upper back between shoulder blades",
    "costas-laser": "upper back between shoulder blades",
    "coxa-cera": "front of the thigh",
    "coxa-laser": "front of the thigh",
    "faixa-cera": "narrow vertical strip on lower abdomen",
    "faixa-linha": "narrow strip on face contour",
    "intergluteos-cera": "upper glute crease area tastefully framed",
    "intergluteos-laser": "upper glute crease area tastefully framed",
    "nariz-cera": "nose entrance area close-up",
    "nariz-laser": "nose entrance area close-up",
    "nadegas-cera": "full buttocks area tastefully framed in white underwear",
    "nadegas-laser": "full buttocks area tastefully framed",
    "meia-nadega-cera": "half buttock area tastefully framed",
    "meia-nadega-laser": "half buttock area tastefully framed",
    "perna-cera": "full leg from thigh to ankle",
    "perna-laser": "full leg from thigh to ankle",
    "meia-perna-cera": "lower half of the leg from knee to ankle",
    "meia-perna-laser": "lower half of the leg from knee to ankle",
    "queixo-cera": "chin area close-up",
    "queixo-laser": "chin area close-up",
    "queixo-linha": "chin area close-up for threading",
    "seios-cera": "chest cleavage / breast contour area tastefully framed",
    "virilha-comum-cera": "bikini line contour tastefully framed in white underwear",
    "virilha-comum-faixa-cera": "bikini line with vertical strip tastefully framed",
    "virilha-cavada-cera": "deeper bikini area tastefully framed in white underwear",
    "virilha-cavada-faixa-cera": "deeper bikini with strip tastefully framed",
    "virilha-modelada-cera": "shaped bikini area tastefully framed",
    "virilha-cera": "full bikini / intimate area tastefully framed in white underwear",
    "virilha-laser": "bikini area tastefully framed",
    "virilha-total-laser": "full intimate area tastefully framed",
    "labios-genitais-cera": "intimate labia area tastefully framed extreme discretion",
    "sobrancelha-cera": "eyebrows close-up",
    "sobrancelha-realce-cera": "eyebrows close-up with defined brows",
    "sobrancelha-henna-simples": "eyebrows close-up henna look",
    "design-sobrancelha": "eyebrows close-up design shape",
    "design-sobrancelha-realce": "eyebrows close-up design and tint",
    "sobrancelha-henna": "eyebrows close-up with henna",
    "realce": "eyebrows close-up soft tint",
    "henna": "eyebrows close-up henna",
    "buço-laser": "upper lip area",  # if typo ids
    "pescoco-laser": "neck / throat area",
    "pescoco-cera": "neck area",
    "orelhas-laser": "ear area close-up",
    "orelha-cera": "ear area close-up",
    "rosto-inteiro-laser": "full face overview",
    "psd-p-laser": "small undefined skin patch on body",
    "psd-m-laser": "medium undefined skin patch on body",
    "psd-g-laser": "large undefined skin patch on body",
    "esfoliacao-faixa": "narrow strip of skin on body for exfoliation",
    "esfoliacao-meio-braco": "half arm for exfoliation",
    "esfoliacao-braco": "full arm for exfoliation",
    "esfoliacao-meia-perna": "half leg for exfoliation",
    "esfoliacao-abdomen": "abdomen for exfoliation",
    "esfoliacao-axilas": "underarm for exfoliation",
    "esfoliacao-costas": "back for exfoliation",
    "esfoliacao-coxa": "thigh for exfoliation",
    "esfoliacao-nadegas": "glutes for exfoliation tastefully framed",
    "esfoliacao-perna": "full leg for exfoliation",
    "esfoliacao-virilha": "bikini line for exfoliation tastefully framed",
    # male-specific bases (id without -masc still)
    "peito-cera": "male chest / pectoral area",
    "peito-laser": "male chest / pectoral area",
    "abdomen-laser": "male abdomen",
    "torax-abdomen-laser": "male chest and abdomen",
    "torax-abdomen-cera": "male chest and abdomen",
    "mamilo-laser": "male nipple area tastefully framed",
    "mamilos-cera": "male nipple area tastefully framed",
    "barba-laser": "beard / jawline area",
    "barba-cera": "beard / jawline area",
    "barba-modeladora-cera": "beard contour lines",
    "bigode-laser": "mustache area",
    "bigode-cera": "mustache area",
    "virilha-comum-cera-masc": "male groin contour tastefully framed in white boxer briefs",
    "saco-escrotal-cera": "male intimate scrotal area extreme discretion white boxer",
    "virilha-laser-masc": "male groin tastefully framed",
}


def method_of(product_id: str) -> str:
    masc = product_id.endswith("-masc")
    base = product_id[: -5] if masc else product_id
    if "esfolia" in base:
        key = "esfoliacao_masc" if masc else "esfoliacao"
    elif "linha" in base:
        key = "linha"
    elif "laser" in base:
        key = "laser_masc" if masc else "laser"
    else:
        # cera family (sobrancelha, henna, etc.)
        key = "cera_masc" if masc else "cera"
    return key


def region_of(product_id: str) -> str:
    base = product_id[: -5] if product_id.endswith("-masc") else product_id
    if base in REGION:
        return REGION[base]
    # fuzzy
    for k, v in REGION.items():
        if k in base or base in k:
            return v
    return "the relevant treatment body area clearly visible"


def prompt_for(product_id: str) -> str:
    masc = product_id.endswith("-masc")
    look = METHOD_LOOK[method_of(product_id)]
    region = region_of(product_id)
    gender = (
        "handsome adult man with short dark hair, white tank top or white boxer briefs as needed for the area"
        if masc
        else "young adult woman with neat hair, white tank top or white underwear as needed for the area"
    )
    return (
        f"Square 1:1 commercial beauty campaign photo for hair-removal ecommerce. "
        f"{gender}. Soft studio lighting. {look[0]}. "
        f"Pose clearly shows: {region}. "
        f"A dashed oval outline in {look[1]} marks exactly that treatment area — "
        f"same dashed-line graphic style as the reference moodboard (small uniform dashes forming an oval). "
        f"Clean spa aesthetic, photorealistic, no text, no logo, no watermark."
    )
