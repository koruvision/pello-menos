from pathlib import Path

p = Path("src/lib/data.ts")
t = p.read_text(encoding="utf-8")
old = 'id: "axilas-laser", name: "Axilas Laser", duration: "15 min • até 10 sessões", originalCents: 89990, category: "axilas", image: catalogImage("axilas-laser"), imageAlt: "Axilas após laser", description: "Descubra a revolucionária depilação a laser para axilas. Resultados eficazes e duradouros. Conquiste axilas suaves e sem pelos. Adquira agora!", badge: "5% OFF"'
new = old.replace('badge: "5% OFF"', 'badge: "60% OFF"')
if old not in t:
    raise SystemExit("not found")
p.write_text(t.replace(old, new, 1), encoding="utf-8")
print("ok")
