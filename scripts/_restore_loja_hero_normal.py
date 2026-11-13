# -*- coding: utf-8 -*-
"""Restaura banners da loja oficial ao estado normal (campaign desktop + mobile baked).

Não altera OficialTeste. Só republica home.html (+ masculino se existir) na loja.
"""
from __future__ import annotations

import base64
import io
import re
import subprocess
import sys
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "src" / "lib" / "data.ts"
HERO = ROOT / "src" / "components" / "HeroBanner.tsx"
EXPORT = ROOT / "scripts" / "export_wp_home.py"
ENV = ROOT / "projeto-migracao" / ".secrets" / "loja.env"
PM = ROOT / "wordpress-loja" / "pm-home"
CLONE = "https://pellomenos.companygenesis.com.br/wp-content/uploads/pm-home"

# Snapshot OT (estado atual desejado no código após o restore da loja)
OT_SLIDES = '''export const heroSlides: HeroSlide[] = [
  {
    id: "verao",
    badge: "Cera 15% OFF",
    title: "Pernas prontas pra viver",
    ...pernaCeraHero,
    cta: "Ver cera",
    ctaHref: "/servicos/cera",
    image: "/images/hero/examples/banner-perna-desktop-fw.jpg",
    imageTablet: "/images/hero/examples/banner-exemplo-avatar-esquerda-tablet.jpg",
    imageMobile: "/images/hero/examples/banner-exemplo-avatar-esquerda.jpg",
    imagePosition: "50% 50%",
    imagePositionMobile: "50% 42%",
    imageAlt: "Mulher na campanha de pernas com cera Pello Menos",
    layout: "copy-top",
    bakedText: true,
  },
  {
    id: "laser-10",
    badge: "Laser 60% OFF",
    title: "10 sessões de laser nas axilas",
    ...axilasLaserHero,
    cta: "Ver laser",
    ctaHref: "/servicos/laser",
    image: "/images/hero/examples/banner-axilas-desktop-fw.jpg",
    imageTablet: "/images/hero/examples/banner-exemplo-avatar-direita-tablet.jpg",
    imageMobile: "/images/hero/examples/banner-exemplo-avatar-direita.jpg",
    imagePosition: "50% 50%",
    imagePositionMobile: "50% 42%",
    imageAlt: "Mulher no centro da campanha de laser nas axilas Pello Menos",
    layout: "split",
    bakedText: true,
  },
  {
    id: "virilha",
    badge: "Esquenta Black",
    title: "Virilha total a laser",
    ...virilhaLaserHero,
    cta: "Ver serviços",
    ctaHref: "/servicos",
    image: "/images/hero/examples/banner-virilha-desktop-fw.jpg",
    imageTablet: "/images/hero/examples/banner-virilha-tablet.jpg",
    imageMobile: "/images/hero/examples/banner-virilha-mobile.jpg",
    imagePosition: "50% 50%",
    imagePositionMobile: "50% 42%",
    imageAlt: "Mulher à esquerda na campanha de virilha a laser Pello Menos",
    layout: "copy-right",
    bakedText: true,
  },
  {
    id: "bracos",
    badge: "Laser 60% OFF",
    title: "Braços inteiros a laser",
    ...bracosLaserHero,
    cta: "Ver braços",
    ctaHref: "/servicos/laser",
    image: "/images/hero/examples/banner-bracos-desktop-fw.jpg",
    imageTablet: "/images/hero/examples/banner-bracos-tablet.jpg",
    imageMobile: "/images/hero/examples/banner-bracos-mobile.jpg",
    imagePosition: "50% 50%",
    imagePositionMobile: "50% 42%",
    imageAlt: "Mulher à direita na campanha de braços a laser Pello Menos",
    layout: "copy-left",
    bakedText: true,
  },
];'''

LOJA_SLIDES = '''export const heroSlides: HeroSlide[] = [
  {
    id: "verao",
    badge: "Cera 15% OFF",
    title: "Pernas prontas pra viver",
    ...pernaCeraHero,
    cta: "Ver cera",
    ctaHref: "/servicos/cera",
    image: "/images/hero/hero-campaign-low.jpg",
    imageMobile: "/images/hero/examples/banner-exemplo-avatar-esquerda.jpg",
    imagePosition: "50% 40%",
    imagePositionMobile: "50% 42%",
    imageAlt: "Mulher na campanha de pernas com cera Pello Menos",
    layout: "copy-top",
    bakedTextMobile: true,
  },
  {
    id: "laser-10",
    badge: "Laser 60% OFF",
    title: "10 sessões de laser nas axilas",
    ...axilasLaserHero,
    cta: "Ver laser",
    ctaHref: "/servicos/laser",
    image: "/images/hero/hero-campaign-center.jpg",
    imageMobile: "/images/hero/examples/banner-exemplo-avatar-direita.jpg",
    imagePosition: "50% 40%",
    imagePositionMobile: "50% 42%",
    imageAlt: "Mulher no centro da campanha de laser nas axilas Pello Menos",
    layout: "split",
    bakedTextMobile: true,
  },
  {
    id: "virilha",
    badge: "Esquenta Black",
    title: "Virilha total a laser",
    ...virilhaLaserHero,
    cta: "Ver serviços",
    ctaHref: "/servicos",
    image: "/images/hero/hero-campaign-left.jpg",
    imageMobile: "/images/hero/examples/banner-virilha-mobile.jpg",
    imagePosition: "62% 42%",
    imagePositionMobile: "50% 42%",
    imageAlt: "Mulher à esquerda na campanha de virilha a laser Pello Menos",
    layout: "copy-right",
    bakedTextMobile: true,
  },
  {
    id: "bracos",
    badge: "Laser 60% OFF",
    title: "Braços inteiros a laser",
    ...bracosLaserHero,
    cta: "Ver braços",
    ctaHref: "/servicos/laser",
    image: "/images/hero/hero-campaign-right.jpg",
    imageMobile: "/images/hero/examples/banner-bracos-mobile.jpg",
    imagePosition: "38% 42%",
    imagePositionMobile: "50% 42%",
    imageAlt: "Mulher à direita na campanha de braços a laser Pello Menos",
    layout: "copy-left",
    bakedTextMobile: true,
  },
];'''

HERO_CLASS_OT = (
    'className="relative aspect-[3/4] w-full overflow-hidden bg-primary '
    'md:aspect-auto md:h-[480px] lg:h-[min(680px,calc(100dvh-10.5rem))]"'
)
HERO_CLASS_LOJA = (
    'className="relative aspect-[3/4] w-full overflow-hidden bg-primary '
    'md:aspect-auto md:h-[480px] lg:h-[560px] xl:h-[600px]"'
)

CSS_OT = """#inicio{position:relative;overflow:hidden;width:100%;aspect-ratio:3/4}
@media (min-width:768px){#inicio{aspect-ratio:auto;height:480px}}
@media (min-width:1024px){#inicio{aspect-ratio:auto;height:min(680px,calc(100dvh - 10.5rem))}}
"""

CSS_LOJA = """#inicio{position:relative;overflow:hidden;width:100%;aspect-ratio:3/4}
@media (min-width:768px){#inicio{aspect-ratio:auto;height:480px}}
@media (min-width:1024px){#inicio{height:560px}}
@media (min-width:1280px){#inicio{height:600px}}
"""


def replace_hero_slides(text: str, block: str) -> str:
    pat = re.compile(
        r"export const heroSlides: HeroSlide\[\] = \[[\s\S]*?\n\];",
        re.M,
    )
    if not pat.search(text):
        raise SystemExit("heroSlides block not found")
    return pat.sub(block.rstrip(), text, count=1)


def load_env():
    vals = {}
    for line in ENV.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        vals[k.strip()] = v.strip()
    return {
        "url": vals["PM_LOJA_URL"].rstrip("/"),
        "user": vals["PM_LOJA_USER"],
        "password": vals["PM_LOJA_APP_PASSWORD"],
    }


def publish_loja_home() -> None:
    c = load_env()
    dest = c["url"] + "/wp-content/uploads/pm-home"
    tok = base64.b64encode(f"{c['user']}:{c['password']}".encode()).decode()
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for name in ("home.html", "masculino.html", "home.css"):
            path = PM / name
            if not path.is_file():
                continue
            raw = path.read_text(encoding="utf-8").replace(CLONE, dest).encode("utf-8")
            z.writestr(name, raw)
            print("zip+", name)
    req = urllib.request.Request(
        c["url"] + "/wp-json/pm-home/v1/bundle",
        data=buf.getvalue(),
        method="POST",
        headers={
            "Authorization": "Basic " + tok,
            "Content-Type": "application/zip",
            "User-Agent": "pm-restore-loja-hero",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=600) as r:
        print("bundle", r.status, r.read()[:160])

    html = (
        urllib.request.urlopen(
            urllib.request.Request(
                c["url"] + "/?v=restore-hero1",
                headers={"User-Agent": "x", "Cache-Control": "no-cache"},
            ),
            timeout=60,
        )
        .read()
        .decode("utf-8", "replace")
    )
    checks = {
        "campaign": "hero-campaign-low" in html,
        "tablet": "banner-exemplo-avatar-esquerda-tablet" in html,
        "desktopExample": "banner-exemplo-avatar-esquerda-desktop" in html,
        "mobileBaked": "banner-exemplo-avatar-esquerda.jpg" in html,
        "jsCopy": "js-hero-copy" in html,
        "ratio16": "aspect-ratio:16/9" in html,
        "h600": "height:600px" in html,
        "arrowsHiddenMobile": 'hidden h-10 w-10 -translate-y-1/2' in html
        or "hidden md:flex" in html
        or 'class="absolute top-1/2 z-20 hidden' in html,
    }
    print("live", checks)
    if not checks["campaign"] or checks["tablet"] or checks["desktopExample"] or checks["ratio16"]:
        raise SystemExit("loja hero restore failed")
    if not checks["arrowsHiddenMobile"]:
        raise SystemExit("hero arrows still visible on mobile markup")

    masc = (
        urllib.request.urlopen(
            urllib.request.Request(
                c["url"] + "/masculino/?v=restore-hero1",
                headers={"User-Agent": "x", "Cache-Control": "no-cache"},
            ),
            timeout=60,
        )
        .read()
        .decode("utf-8", "replace")
    )
    masc_checks = {
        "peitoDesktop": "hero-peito.jpg" in masc,
        "peitoMobileCrop": "hero-peito-m.jpg" in masc,
        "promoLaserOld": "promo-laser-v5" in masc,
        "arrowsHiddenMobile": 'class="absolute top-1/2 z-20 hidden' in masc,
        "laserTitle": "Laser masculino" in masc,
    }
    print("masc", masc_checks)
    if (
        not masc_checks["peitoDesktop"]
        or masc_checks["peitoMobileCrop"]
        or masc_checks["promoLaserOld"]
        or not masc_checks["arrowsHiddenMobile"]
    ):
        raise SystemExit("masculino hero/promo/arrows failed")
    print("LOJA_HERO_NORMAL_OK", c["url"] + "/?v=restore-hero1")


def main() -> None:
    data = DATA.read_text(encoding="utf-8")
    hero = HERO.read_text(encoding="utf-8")
    export = EXPORT.read_text(encoding="utf-8")

    try:
        # 1) estado loja normal
        DATA.write_text(replace_hero_slides(data, LOJA_SLIDES), encoding="utf-8")
        HERO.write_text(hero.replace(HERO_CLASS_OT, HERO_CLASS_LOJA), encoding="utf-8")
        if CSS_OT not in export:
            raise SystemExit("CSS_OT marker missing in export_wp_home.py")
        EXPORT.write_text(export.replace(CSS_OT, CSS_LOJA), encoding="utf-8")

        subprocess.check_call(
            [sys.executable, str(ROOT / "scripts" / "_export_home_and_masc.py")],
            cwd=str(ROOT),
        )
        publish_loja_home()
    finally:
        # 2) devolve código ao estado OT (experimentos de banner)
        DATA.write_text(replace_hero_slides(DATA.read_text(encoding="utf-8"), OT_SLIDES), encoding="utf-8")
        # re-read in case partial writes
        h = HERO.read_text(encoding="utf-8")
        if HERO_CLASS_LOJA in h:
            HERO.write_text(h.replace(HERO_CLASS_LOJA, HERO_CLASS_OT), encoding="utf-8")
        e = EXPORT.read_text(encoding="utf-8")
        if CSS_LOJA in e and CSS_OT not in e:
            EXPORT.write_text(e.replace(CSS_LOJA, CSS_OT), encoding="utf-8")
        subprocess.check_call(
            [sys.executable, str(ROOT / "scripts" / "_export_home_and_masc.py")],
            cwd=str(ROOT),
        )
        print("code+local export restored to OT hero config")


if __name__ == "__main__":
    main()
