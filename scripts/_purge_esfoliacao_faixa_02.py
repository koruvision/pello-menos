# -*- coding: utf-8 -*-
"""Remove esfoliacao-faixa-02 (+ masc) from catalog artifacts; save snapshot."""
from __future__ import annotations

import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KEYS = ("esfoliacao-faixa-02", "esfoliacao-faixa-02-masc")
SNAPSHOT = ROOT / "projeto-migracao" / ".secrets" / "faixa-02-purged-restore.json"

COPY = ROOT / "src" / "lib" / "product-copy.json"
BRIDGE = ROOT / "src" / "lib" / "woo-bridge.json"
BRIDGE_WP = ROOT / "wordpress-loja" / "pm-home" / "woo-bridge.json"


def main():
    copy = json.loads(COPY.read_text(encoding="utf-8"))
    bridge = json.loads(BRIDGE.read_text(encoding="utf-8"))

    snap = {
        "purged_at": "2026-10-26",
        "reason": "Faixa 02 não deve mais existir (fem + masc). Pedido alinhamento catálogo.",
        "how_to_restore": "Reinserir product_copy e bridge keys; seed em data.ts se necessário.",
        "product_copy": {},
        "woo_bridge": {},
        "data_ts_seeds": {
            "esfoliacao-faixa-02": '{ id: "esfoliacao-faixa-02", name: "Esfoliação Faixa 02", duration: "10 min • Avulso", originalCents: 2400, category: "corpo", image: catalogImage("esfoliacao-faixa-02"), imageAlt: "Esfoliação de faixa 02", method: "esfoliacao" },',
            "esfoliacao-faixa-02-masc": '{ id: "esfoliacao-faixa-02-masc", name: "Esfoliação Faixa 02", duration: "10 min • Avulso", originalCents: 3700, category: "corpo", image: catalogImage("esfoliacao-faixa-02-masc", "masculino"), imageAlt: "Esfoliação de faixa 02 masculina Pello Menos", method: "esfoliacao", audience: "masculino" },',
        },
        "note": "Não apagar Woo faixa-cera (shared). Imagens public podem ficar órfãs.",
    }

    for k in KEYS:
        if k in copy:
            snap["product_copy"][k] = copy.pop(k)
            print("copy removed", k)
        if k in bridge:
            snap["woo_bridge"][k] = bridge.pop(k)
            print("bridge removed", k)

    SNAPSHOT.parent.mkdir(parents=True, exist_ok=True)
    SNAPSHOT.write_text(json.dumps(snap, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    COPY.write_text(json.dumps(copy, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    BRIDGE.write_text(json.dumps(bridge, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    shutil.copyfile(BRIDGE, BRIDGE_WP)
    print("snapshot", SNAPSHOT)
    print("DONE")


if __name__ == "__main__":
    main()
