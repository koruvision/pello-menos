# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSS = ROOT / "wordpress-loja" / "pm-home" / "home.css"
MARKER = "/* pm-cursor-pointer */"
BLOCK = """
/* pm-cursor-pointer */
a[href],
button:not(:disabled),
[role="button"]:not([aria-disabled="true"]),
.btn-lux,
input[type="submit"]:not(:disabled),
input[type="button"]:not(:disabled),
input[type="reset"]:not(:disabled),
label[for],
summary,
select,
[data-pm-add],
[data-pm-related-add],
[data-pm-upsell-add],
[data-dec],
[data-inc],
[data-clear],
[data-pm-coupon-apply],
[data-pm-coupon-remove],
[data-pm-more-toggle] {
  cursor: pointer;
}
button:disabled,
.btn-lux:disabled,
a[aria-disabled="true"],
[aria-disabled="true"],
input:disabled {
  cursor: not-allowed;
}
"""


def bump_css_version(html: str) -> str:
    for old, new in (
        ("home.css?v=premium3", "home.css?v=premium4"),
        ("home.css?v=premium2", "home.css?v=premium4"),
        ("home.css?v=premium4", "home.css?v=premium4"),
    ):
        html = html.replace(old, new)
    # bare link without query
    if "home.css?v=" not in html and 'home.css"' in html:
        html = html.replace('home.css"', 'home.css?v=premium4"')
    return html


def main() -> None:
    text = CSS.read_text(encoding="utf-8")
    if MARKER in text:
        text = text[: text.index(MARKER)].rstrip() + "\n" + BLOCK
    else:
        text = text.rstrip() + "\n" + BLOCK
    CSS.write_text(text, encoding="utf-8")
    print("patched", CSS, "bytes", CSS.stat().st_size)

    n = 0
    pm = ROOT / "wordpress-loja" / "pm-home"
    for path in list(pm.rglob("*.html")):
        raw = path.read_text(encoding="utf-8")
        nxt = bump_css_version(raw)
        # also ensure social product first paint
        nxt = nxt.replace(
            "/images/social/cliente-1.png",
            "/images/products/axilas-laser.png",
        )
        if nxt != raw:
            path.write_text(nxt, encoding="utf-8")
            n += 1
    print("html_bumped", n)

    export = ROOT / "scripts" / "export_wp_home.py"
    if export.exists():
        et = export.read_text(encoding="utf-8")
        et2 = et.replace("home.css?v=premium3", "home.css?v=premium4").replace(
            "home.css?v=premium2", "home.css?v=premium4"
        )
        if et2 != et:
            export.write_text(et2, encoding="utf-8")
            print("export_wp_home css version bumped")


if __name__ == "__main__":
    main()
