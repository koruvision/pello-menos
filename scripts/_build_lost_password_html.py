# -*- coding: utf-8 -*-
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
src = (ROOT / "wordpress-loja/pm-home/conta.html").read_text(encoding="utf-8")
start = src.find("<main")
end = src.find("</main>") + len("</main>")
body = (
    '<main class="mx-auto w-full max-w-md px-container-margin py-16">\n'
    "  <!--PM_LOST_BODY-->\n"
    "</main>"
)
out = src[:start] + body + src[end:]
out = re.sub(
    r'<script src="[^"]*/pm-home/account\.js\?v=[^"]+"></script>\s*',
    "",
    out,
)
out = re.sub(
    r"<title>[^<]*</title>",
    "<title>Perdeu sua senha | Pello Menos</title>",
    out,
    count=1,
)
dest = ROOT / "wordpress-loja/pm-home/lost-password.html"
dest.write_text(out, encoding="utf-8")
print("wrote", dest, "bytes", len(out), "placeholder", "<!--PM_LOST_BODY-->" in out)
