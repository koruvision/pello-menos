"""Splice catalog fragment and helpers into src/lib/data.ts."""
from pathlib import Path

root = Path(__file__).resolve().parents[1]
p = root / "src" / "lib" / "data.ts"
text = p.read_text(encoding="utf-8")
start = text.index("const I = {")
end = text.index("function defaultDescription")
m_start = text.index("const M = {")
m_end = text.index("const catalogItems: ProductSeed[]")
m_block = text[m_start:m_end]
fragment = (root / "scripts" / "_catalog_fragment.ts").read_text(encoding="utf-8")
helper = """const MALE_CANONICAL_IMAGES: Record<string, string> = {
  "peito-cera-masc": "/images/products/male/peito.jpg",
  "abdomen-cera-masc": "/images/products/male/abdomen.jpg",
  "axila-cera-masc": "/images/products/male/axilas.jpg",
  "antebraco-cera-masc": "/images/products/male/antebraco.jpg",
  "bracos-cera-masc": "/images/products/male/bracos.jpg",
  "costas-cera-masc": "/images/products/male/costas.jpg",
  "perna-cera-masc": "/images/products/male/pernas.jpg",
  "virilha-cera-masc": "/images/products/male/virilha.jpg",
  "queixo-cera-masc": "/images/products/male/barba.jpg",
  "nuca-laser-masc": "/images/products/male/nuca.jpg",
  "pescoco-laser-masc": "/images/products/male/pescoco.jpg",
};

export function catalogImage(id: string, audience: ProductAudience = "feminino") {
  if (audience === "masculino") {
    return MALE_CANONICAL_IMAGES[id] ?? `/images/products/male/${id}.png`;
  }
  return `/images/products/${id}.png`;
}

"""
out = text[:start] + helper + m_block + fragment + "\n\n" + text[end:]
out = out.replace(
    "const pernaCeraHero = formatHeroPrice(8700);",
    "const pernaCeraHero = formatHeroPrice(8590);",
)
out = out.replace(
    """export const categories: Category[] = [
  { id: "virilha", label: "Virilha", image: I.virilhaCera, href: areaHref("feminino", "virilha") },
  { id: "pernas", label: "Pernas", image: I.pernaCera, href: areaHref("feminino", "pernas") },
  { id: "axilas", label: "Axilas", image: I.axilaCera, href: areaHref("feminino", "axilas") },
  { id: "rosto", label: "Rosto", image: I.rostoLaser, href: areaHref("feminino", "rosto") },
  { id: "corpo", label: "Corpo", image: I.abdomenCera, href: areaHref("feminino", "corpo") },
];""",
    """export const categories: Category[] = [
  { id: "virilha", label: "Virilha", image: catalogImage("virilha-cera"), href: areaHref("feminino", "virilha") },
  { id: "pernas", label: "Pernas", image: catalogImage("perna-cera"), href: areaHref("feminino", "pernas") },
  { id: "axilas", label: "Axilas", image: catalogImage("axila-cera"), href: areaHref("feminino", "axilas") },
  { id: "rosto", label: "Rosto", image: catalogImage("rosto-inteiro-laser"), href: areaHref("feminino", "rosto") },
  { id: "corpo", label: "Corpo", image: catalogImage("abdomen-cera"), href: areaHref("feminino", "corpo") },
];""",
)
p.write_text(out, encoding="utf-8")
print("wrote", p)
print("I leftover", out.count("I."))
print("tintura", "tintura-pelos" in out)
