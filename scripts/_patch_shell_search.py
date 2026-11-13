# -*- coding: utf-8 -*-
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "wordpress-loja" / "pm-home"

NEEDLE = (
    'form.action = "/";\n'
    '        form.method = "get";\n'
    "        form.className =\n"
    '          "fixed inset-x-0 top-[154px] z-[90] border-b border-outline/40 bg-white px-container-margin py-4 md:top-[164px]";\n'
    "        form.innerHTML =\n"
    "          '<input name=\"s\" type=\"search\" placeholder=\"Buscar serviços\" class=\"w-full rounded-full border border-primary/25 px-4 py-3 text-sm text-on-surface outline-none\" />';"
)

REPL = (
    'form.action = "/busca";\n'
    '        form.method = "get";\n'
    "        form.className =\n"
    '          "fixed inset-x-0 top-[154px] z-[90] border-b border-outline/40 bg-white px-container-margin py-4 md:top-[164px]";\n'
    "        form.innerHTML =\n"
    "          '<input name=\"q\" type=\"search\" placeholder=\"Buscar serviços\" class=\"w-full rounded-full border border-primary/25 px-4 py-3 text-sm text-on-surface outline-none\" required />';"
)


def main():
    n = 0
    for path in sorted(ROOT.glob("checkout-shell*.js")):
        text = path.read_text(encoding="utf-8")
        if NEEDLE not in text:
            # try simpler replace pieces
            if 'name="s"' in text and 'form.action = "/"' in text:
                text2 = text.replace('form.action = "/";', 'form.action = "/busca";')
                text2 = text2.replace(
                    '<input name="s" type="search" placeholder="Buscar serviços" class="w-full rounded-full border border-primary/25 px-4 py-3 text-sm text-on-surface outline-none" />',
                    '<input name="q" type="search" placeholder="Buscar serviços" class="w-full rounded-full border border-primary/25 px-4 py-3 text-sm text-on-surface outline-none" required />',
                )
                if text2 != text:
                    path.write_text(text2, encoding="utf-8")
                    n += 1
                    print("OK-simple", path.name)
                else:
                    print("MISS", path.name)
            else:
                print("MISS", path.name)
            continue
        path.write_text(text.replace(NEEDLE, REPL), encoding="utf-8")
        n += 1
        print("OK", path.name)
    print("patched", n)


if __name__ == "__main__":
    main()
