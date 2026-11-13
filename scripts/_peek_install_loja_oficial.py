# -*- coding: utf-8 -*-
"""Read-only: compare installment CF7CF rules on oficialteste vs loja oficial."""
import json
import re
import urllib.request

SITES = {
    "oficialteste": "https://pellomenosoficialteste.companygenesis.com.br/finalizar-pagamento/?pm=inst-cmp",
    "loja": "https://loja.pellomenos.com.br/finalizar-pagamento/?pm=inst-cmp",
}


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; pm-read/1.0)"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode("utf-8", "replace")


def select_options(html, name):
    m = re.search(
        rf'<select[^>]*name="{name}"[^>]*>([\s\S]*?)</select>',
        html,
        re.I,
    )
    if not m:
        return None
    return re.findall(r'<option[^>]*value="([^"]*)"[^>]*>([^<]*)</option>', m.group(1), re.I)


def conds(html):
    m = re.search(r'name="_wpcf7cf_options"[^>]*value="([^"]*)"', html)
    if not m:
        return None
    raw = m.group(1).replace("&quot;", '"').replace("&amp;", "&")
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return {"parse_error": True, "raw_len": len(raw)}
    out = []
    for c in data.get("conditions") or []:
        then = c.get("then_field") or ""
        if then in ("productcera", "nosubscribe", "subscribe", "allunits", "laserunits"):
            out.append(c)
    return out


def main():
    snaps = {}
    for label, url in SITES.items():
        print("===", label)
        try:
            html = fetch(url)
        except Exception as e:
            print("FETCH_FAIL", type(e).__name__, e)
            continue
        print("len", len(html), "wpcf7-f1831", "wpcf7-f1831" in html)
        for name in ("installments", "allinstallments", "cerainstallments", "siteinstallment"):
            opts = select_options(html, name)
            if opts is None:
                # hidden input
                hm = re.search(rf'name="{name}"[^>]*value="([^"]*)"', html)
                print(f"  {name}:", "hidden" if hm else "MISSING", hm.group(1) if hm else "")
            else:
                print(f"  {name}:", [v for v, _t in opts])
        c = conds(html)
        snaps[label] = c
        if c is None:
            print("  CF7CF: missing")
        elif isinstance(c, dict) and c.get("parse_error"):
            print("  CF7CF: parse_error", c)
        else:
            print("  CF7CF conditions:", len(c))
            for row in c:
                print("   ", json.dumps(row, ensure_ascii=False))

    if "oficialteste" in snaps and "loja" in snaps:
        a = json.dumps(snaps["oficialteste"], ensure_ascii=False, sort_keys=True)
        b = json.dumps(snaps["loja"], ensure_ascii=False, sort_keys=True)
        print("CONDITIONS_EQUAL", a == b)


if __name__ == "__main__":
    main()
