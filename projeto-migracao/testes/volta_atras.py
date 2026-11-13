# -*- coding: utf-8 -*-
import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _comum import BASE, OUT, REF, ENV_FILE, read_env, cart_state, clear_cart, choose_unit, add_current, local_cart  # noqa: E402
import subprocess, sys, time, urllib.request, re
ROOT = str(Path(__file__).resolve().parents[2])
ENVF = str(ENV_FILE)


def snap(tag):
    out = {}
    for path, key in (("/", "home"), ("/carrinho/", "carrinho"), ("/minha-conta/", "conta"), ("/finalizar-pagamento/", "pay")):
        req = urllib.request.Request(f"{BASE}{path}?pm={tag}", headers={"User-Agent": "pm"})
        with urllib.request.urlopen(req, timeout=120) as r:
            html = r.read().decode("utf-8", "replace")
            out[key] = ("projeto" if "pm-home" in html and "checkout-shell" not in html else ("tema+shell" if "checkout-shell" in html else "tema")) + f" {r.status}"
    return out


def pub(*args):
    t = time.time()
    res = subprocess.run([sys.executable, "scripts/pm_publicar_destino.py", "--env", ENVF, "snippet", *args], cwd=ROOT, capture_output=True, text=True)
    print("  ", res.stdout.strip().splitlines()[-2] if res.stdout else res.stderr[:200], f"({time.time()-t:.1f}s)")


tag = str(int(time.time()))
print("antes:", snap(tag + "a"))
t0 = time.time()
pub("--off")
print(f"depois de --off ({time.time()-t0:.1f}s):", snap(tag + "b"))
t0 = time.time()
pub("--routes=home,masculino,produto,carrinho,conta,shell")
print(f"depois de religar ({time.time()-t0:.1f}s):", snap(tag + "c"))
