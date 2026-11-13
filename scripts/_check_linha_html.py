from pathlib import Path

p = Path("wordpress-loja/pm-home/products/buco-linha.html")
t = p.read_text(encoding="utf-8") if p.exists() else ""
print("exists", p.exists(), "len", len(t))
print("goncalo", "goncalo" in t.lower() or "gonçalo" in t.lower())
print("Afonso", "Afonso" in t)
print("Treze", "Treze" in t)
print("sgo id", 'data-unit-id="sgo"' in t or 'value="sgo"' in t)
# bridge copy
b = Path("wordpress-loja/pm-home/woo-bridge.json")
import json

br = json.loads(b.read_text(encoding="utf-8"))
u = br["buco-linha"]["units"]
print("bridge linha", len(u), "ape" in u, "13m" in u, "sgo" in u)
