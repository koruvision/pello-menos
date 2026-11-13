"""Render the two homes from the local Next server into static documents."""

import hashlib
import json
import os
import re
import shutil
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# PM_OUT permite exportar para uma pasta temporária e comparar antes de publicar.
OUT = Path(os.environ.get("PM_OUT") or (ROOT / "wordpress-loja" / "pm-home"))
PUBLIC = ROOT / "public"
ORIGIN = os.environ.get("PM_HOME_ORIGIN", "http://127.0.0.1:3456")
ASSET_BASE = os.environ.get(
    "PM_ASSET_BASE",
    "https://loja.pellomenos.com.br/wp-content/uploads/pm-home",
).rstrip("/")
WOO = os.environ.get("PM_WOO_ORIGIN", "https://loja.pellomenos.com.br")
GTM_ID = os.environ.get("PM_GTM_ID", "GTM-52G8XVQ8")

GTM_HEAD = f"""<!-- Google Tag Manager -->
<script>(function(w,d,s,l,i){{w[l]=w[l]||[];w[l].push({{'gtm.start':
new Date().getTime(),event:'gtm.js'}});var f=d.getElementsByTagName(s)[0],
j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src=
'https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);
}})(window,document,'script','dataLayer','{GTM_ID}');</script>
<!-- End Google Tag Manager -->
"""

GTM_BODY = f"""<!-- Google Tag Manager (noscript) -->
<noscript><iframe src="https://www.googletagmanager.com/ns.html?id={GTM_ID}"
height="0" width="0" style="display:none;visibility:hidden"></iframe></noscript>
<!-- End Google Tag Manager (noscript) -->
"""

PAGE_LINKS = {
    "/carrinho": "/carrinho/",
}


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "pm-home-export"})
    with urllib.request.urlopen(req, timeout=120) as response:
        return response.read()


def woo_slugs():
    slugs = set()
    user = os.environ.get("PM_WOO_USER", "")
    password = os.environ.get("PM_WOO_PASS", "")
    auth = ""
    if user and password:
        import base64

        token = base64.b64encode(f"{user}:{password}".encode()).decode()
        auth = "Basic " + token
    page = 1
    while page <= 40:
        if auth:
            url = (
                f"{WOO}/wp-json/wc/v3/products?per_page=100&page={page}"
                "&status=publish&_fields=slug"
            )
        else:
            url = f"{WOO}/wp-json/wc/store/v1/products?per_page=100&page={page}"
        req = urllib.request.Request(url, headers={"User-Agent": "pm-home-export"})
        if auth:
            req.add_header("Authorization", auth)
        try:
            with urllib.request.urlopen(req, timeout=60) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except Exception as error:
            print("woo page", page, type(error).__name__)
            break
        if not payload:
            break
        for item in payload:
            slug = item.get("slug") or ""
            if slug:
                slugs.add(slug)
        if len(payload) < 100:
            break
        page += 1
    print("woo slugs", len(slugs))
    return slugs


ALIASES = {
    "plano-silver": "plano-de-assinatura-vip-silver-copia-2",
    "plano-gold": "plano-de-assinatura-vip-gold",
    "plano-clube-laser": "clube-do-laser",
    "plano-prepago": "pre-pago-pello-menos",
    "perna-laser": "perna-inteira-laser-2",
    "perna-cera": "perna-inteira-cera",
    "bracos-laser": "bracos-inteiros-laser-2",
    "nadegas-cera": "nadegas-completas-cera",
    "design-sobrancelha": "design-de-sobrancelha-cera",
    "rosto-inteiro-laser": "rosto-inteiro-laser-buqunzpsd-p",
    "virilha-faixa-laser": "virilha-c-faixa-laser-2",
    "virilha-cavada-faixa-laser": "virilha-cavada-c-faixa-laser-2",
    "axila-laser": "axilas-laser-2",
    "virilha-cera": "virilha-total-cera",
    "virilha-comum-laser": "virilha-laser-2",
    "coxa-laser": "coxas-laser",
    "sobrancelha-henna": "sobrancelha-henna-cera",
    "sobrancelha-henna-simples": "design-de-sobrancelha-henna-cera",
}


EXTRA = {
    "design-sobrancelha-realce": "design-de-sobrancelha-realce-cera",
    "areola-laser": "aureola-laser-2",
    "peito-cera-masc": "abdomen-cera-2",
    "peito-laser-masc": "abdomen-laser-2",
    "barba-laser-masc": "rosto-inteiro-laser-buqunzpsd-p",
    "bigode-laser-masc": "buco-laser-2",
    "torax-abdomen-laser-masc": "abdomen-laser-2",
    "mamilo-laser-masc": "aureola-laser-2",
    "virilha-total-laser-masc": "virilha-laser-2",
}

ESFOLIACAO = {
    "axilas": "axila-cera",
    "virilha": "virilha-total-cera",
    "virilha-faixa": "virilha-comum-faixa-cera",
    "perna": "perna-inteira-cera",
    "meia-perna": "meia-perna-cera",
    "faixa": "faixa-cera",
    "braco": "bracos-cera",
    "meio-braco": "antebraco-cera",
    "abdomen": "abdomen-cera-2",
    "nadegas": "nadegas-completas-cera",
    "meia-nadega": "meia-nadega-cera",
    "coxa": "coxa-cera",
    "costas": "costas-cera",
    "seios": "seios-cera",
}


def resolve_product(slug, slugs):
    original = slug
    if slug.startswith("body-splash") or slug.startswith("cartao-presente"):
        return "/loja/"
    slug = EXTRA.get(slug, slug)
    if slug.endswith("-masc"):
        slug = slug[: -len("-masc")]
    slug = ALIASES.get(slug, slug)
    if slug.startswith("esfoliacao-"):
        slug = ESFOLIACAO.get(slug[len("esfoliacao-") :], slug)
    candidates = [slug, f"{slug}-2"]
    for candidate in candidates:
        if candidate in slugs:
            return f"/produto/{candidate}/"
    print("fallback", original)
    if "axila-cera" in slugs:
        return "/produto/axila-cera/"
    return "/loja/"


def rewrite_href(href, slugs):
    if href.startswith("#") or href.startswith("mailto:") or href.startswith("tel:"):
        return href
    if href.startswith("http://") or href.startswith("https://"):
        return href
    path = href.split("?")[0].split("#")[0]
    if path != "/" and path.endswith("/"):
        path = path[:-1]
    if path in PAGE_LINKS:
        return PAGE_LINKS[path]
    if path.startswith("/produto/"):
        slug = path[len("/produto/") :].strip("/")
        return f"/produto/{slug}/"
    return href


def rewrite_links(html, slugs):
    def repl(match):
        quote = match.group(1)
        href = match.group(2)
        return f"href={quote}{rewrite_href(href, slugs)}{quote}"

    return re.sub(r"href=(['\"])([^'\"]+)\1", repl, html)


def original_public_path(url):
    url = url.strip().strip("'\"")
    if not url or url.startswith("data:"):
        return None
    if url.startswith(ASSET_BASE):
        return None
    parsed = urllib.parse.urlparse(url)
    if parsed.path.endswith("/_next/image"):
        query = urllib.parse.parse_qs(parsed.query)
        raw = query.get("url", [""])[0]
        return urllib.parse.unquote(raw)
    if parsed.path.startswith("/images/") or parsed.path.startswith("/brand/"):
        return parsed.path
    return None


_MEDIA_VERSION_CACHE: dict = {}


def media_version(local):
    """Hash curto do conteÃºdo: a CDN (hcdn) guarda /media por 7 dias e sem query
    o navegador continuava recebendo a foto antiga depois de trocar o arquivo."""
    key = str(local)
    if key not in _MEDIA_VERSION_CACHE:
        _MEDIA_VERSION_CACHE[key] = hashlib.md5(local.read_bytes()).hexdigest()[:8]
    return _MEDIA_VERSION_CACHE[key]


def media_url(path):
    local = PUBLIC / path.lstrip("/")
    return f"{ASSET_BASE}/media{path}?v={media_version(local)}"


def collect_and_rewrite_assets(html, copied):
    def replace_url(url):
        path = original_public_path(url)
        if not path:
            return url
        local = PUBLIC / path.lstrip("/")
        if not local.is_file():
            print("missing asset", path)
            return url
        dest = OUT / "media" / path.lstrip("/")
        dest.parent.mkdir(parents=True, exist_ok=True)
        if path not in copied:
            shutil.copy2(local, dest)
            copied.add(path)
        return media_url(path)

    def src_repl(match):
        attr = match.group(1)
        quote = match.group(2)
        value = match.group(3)
        parts = []
        for piece in value.split(","):
            chunk = piece.strip()
            if not chunk:
                continue
            bits = chunk.split()
            bits[0] = replace_url(bits[0])
            parts.append(" ".join(bits))
        return f"{attr}={quote}{', '.join(parts)}{quote}"

    html = re.sub(
        r"(?i)(src|srcset|href)=(['\"])([^'\"]+)\2",
        src_repl,
        html,
    )
    return html


def css_links(html):
    hrefs = []
    for tag in re.findall(r"<link\b[^>]*>", html):
        if "stylesheet" not in tag:
            continue
        match = re.search(r'href="([^"]+)"', tag)
        if match:
            hrefs.append(match.group(1))
    return hrefs


def rewrite_font_urls(css, base_url):
    fonts = {}

    def font_repl(match):
        raw = match.group(1).strip().strip("'\"")
        if raw.startswith("data:") or "uploads/pm-home/fonts/" in raw:
            return match.group(0)
        if not re.search(r"\.(?:woff2?|ttf|otf|eot)(?:\?|$)", raw, re.I):
            return match.group(0)
        absolute = urllib.parse.urljoin(base_url, raw)
        name = Path(urllib.parse.urlparse(absolute).path).name
        if name not in fonts:
            dest = OUT / "fonts" / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(fetch(absolute))
            fonts[name] = f"{ASSET_BASE}/fonts/{name}"
        return f"url({fonts[name]})"

    return re.sub(r"url\(([^)]+)\)", font_repl, css)


def pull_css(html):
    chunks = []
    for href in css_links(html):
        url = urllib.parse.urljoin(ORIGIN + "/", href)
        text = fetch(url).decode("utf-8", "replace")
        chunks.append(rewrite_font_urls(text, url))
    for style in re.findall(r"<style\b[^>]*>(.*?)</style>", html, flags=re.S):
        if "font" in style or "--font" in style or "@font-face" in style:
            chunks.append(rewrite_font_urls(style, ORIGIN + "/"))
    return "\n".join(chunks)


MASC_HEAD_SCRIPT = """<script>
(function(){
  try {
    var path = (location.pathname||"/").replace(/\\/$/,"")||"/";
    if (!/\\/produto\\/[^/]+-masc$/.test(path)) return;
    var root = document.documentElement;
    document.addEventListener("DOMContentLoaded", function(){
      var node = document.querySelector("[data-audience]");
      if (node && node.getAttribute("data-audience") !== "masculino") {
        node.setAttribute("data-audience", "masculino");
      }
    });
    // Marca cedo para CSS [data-audience=masculino] se o root jÃ¡ existir no parse
  } catch (e) {}
})();
</script>
"""


def force_masculino_audience(body: str) -> str:
    """Bake masculine theme into static product HTML to avoid femininoâ†’masculino flash."""
    body = body.replace('data-audience="feminino"', 'data-audience="masculino"', 1)
    active = (
        "rounded-full bg-primary px-5 py-1.5 text-xs font-semibold "
        "tracking-wide text-on-primary uppercase"
    )
    inactive = (
        "rounded-full px-5 py-1.5 text-xs font-semibold tracking-wide "
        "text-primary uppercase hover:bg-primary/10"
    )
    # Feminino link: force inactive
    body = re.sub(
        rf'(<a([^>]*\s)?href="/"(?!masculino)([^>]*)\sclass="){re.escape(active)}(")',
        rf"\1{inactive}\4",
        body,
        count=1,
    )
    # Masculino link: force active
    body = re.sub(
        rf'(<a([^>]*\s)?href="/masculino/?"([^>]*)\sclass="){re.escape(inactive)}(")',
        rf"\1{active}\4",
        body,
        count=1,
    )
    return body


def extract_document(html, title, extra_scripts=(), product_id=None):
    html_class = ""
    match = re.search(r"<html\b[^>]*\bclass=\"([^\"]*)\"", html)
    if match:
        html_class = match.group(1)
    body_attrs = ""
    match = re.search(r"<body\b([^>]*)>", html)
    if match:
        body_attrs = match.group(1)
    body_match = re.search(r"<body\b[^>]*>(.*)</body>", html, flags=re.S)
    body = body_match.group(1) if body_match else html
    body = re.sub(r"<script\b[^>]*>.*?</script>", "", body, flags=re.S)
    body = re.sub(r"<next-route-announcer\b[^>]*>.*?</next-route-announcer>", "", body, flags=re.S)
    body = re.sub(r"<link\b[^>]*>", "", body)
    # WhatsApp flutuante vem sÃ³ do whatsapp-float.js (evita botÃ£o duplicado no HTML estÃ¡tico).
    body = re.sub(
        r'<div class="pointer-events-none fixed bottom-24 (?:left|right)-4 z-\[70\][^"]*"[^>]*>.*?'
        r'aria-label="WhatsApp SAC Pello Menos".*?</a>\s*</div>',
        "",
        body,
        count=1,
        flags=re.S,
    )
    is_masc = bool(product_id and str(product_id).endswith("-masc"))
    if is_masc:
        body = force_masculino_audience(body)
    head_extra = MASC_HEAD_SCRIPT if is_masc else ""
    return f"""<!DOCTYPE html>
<html lang="pt-BR" class="{html_class}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<link rel="icon" href="https://loja.pellomenos.com.br/wp-content/uploads/2021/04/cropped-favicon-50x50.png" sizes="32x32">
<link rel="icon" href="https://loja.pellomenos.com.br/wp-content/uploads/2021/04/cropped-favicon-300x300.png" sizes="192x192">
<link rel="apple-touch-icon" href="https://loja.pellomenos.com.br/wp-content/uploads/2021/04/cropped-favicon-300x300.png">
<link rel="stylesheet" href="{ASSET_BASE}/home.css?v=premium6">
{GTM_HEAD}{head_extra}</head>
<body{body_attrs}>
{GTM_BODY}{body}
<script src="https://cdn.jsdelivr.net/npm/gsap@3.15.0/dist/gsap.min.js"></script>
<script src="{ASSET_BASE}/home.js?v=premium7"></script>
<script src="{ASSET_BASE}/whatsapp-float.js?v=wa7"></script>
<script src="{ASSET_BASE}/promo-popup.js?v=promo3"></script>
{"".join(extra_scripts)}
</body>
</html>
"""


SHARED_CHROME_TWIN_IDS = (
    "body-splash-livre",
    "body-splash-marcante",
    "body-splash-autentica",
    "cartao-presente",
    "cartao-presente-160",
    "cartao-presente-215",
    "cartao-presente-290",
    "plano-silver",
    "plano-gold",
    "plano-prepago",
)


def catalog_ids():
    text = (ROOT / "src" / "lib" / "data.ts").read_text(encoding="utf-8")
    chunk = text.split("const catalogItems")[1].split("function defaultDescription")[0]
    ids = re.findall(r'\bid: "([^"]+)"', chunk)
    # Runtime twins (`expandCatalogWithAudienceTwins`) are not in catalogItems literals.
    for base in SHARED_CHROME_TWIN_IDS:
        twin = f"{base}-masc"
        if base in ids and twin not in ids:
            ids.append(twin)
    return ids


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "products").mkdir(parents=True, exist_ok=True)
    slugs = woo_slugs()
    (OUT / "woo-slugs.json").write_text(
        json.dumps(sorted(slugs), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    bridge_path = ROOT / "src" / "lib" / "woo-bridge.json"
    bridge = {}
    if bridge_path.is_file():
        bridge = json.loads(bridge_path.read_text(encoding="utf-8"))
    copied = set()
    css = ""
    product_scripts = (
        f'<script src="{ASSET_BASE}/product.js?v=units5"></script>\n',
    )
    cart_scripts = product_scripts + (
        f'<script src="{ASSET_BASE}/black-nov-campaign.js?v=black2"></script>\n',
        f'<script src="{ASSET_BASE}/cart.js?v=cart29"></script>\n',
    )
    busca_scripts = (
        f'<script src="{ASSET_BASE}/busca.js?v=busca3"></script>\n',
    )
    pages = [
        ("/", "home.html", "Pello Menos - Depilação", ()),
        ("/masculino", "masculino.html", "Masculino | Pello Menos", ()),
        ("/carrinho", "carrinho.html", "Carrinho | Pello Menos", cart_scripts),
        ("/busca", "busca.html", "Busca | Pello Menos", busca_scripts),
        ("/loja", "pages/loja.html", "Loja | Pello Menos", ()),
        ("/servicos", "pages/servicos.html", None, ()),
        ("/servicos/cera", "pages/servicos-cera.html", None, ()),
        ("/servicos/laser", "pages/servicos-laser.html", None, ()),
        ("/servicos/linha", "pages/servicos-linha.html", None, ()),
        ("/servicos/esfoliacao", "pages/servicos-esfoliacao.html", None, ()),
        ("/masculino/servicos", "pages/masculino-servicos.html", None, ()),
        ("/masculino/servicos/cera", "pages/masculino-servicos-cera.html", None, ()),
        ("/masculino/servicos/laser", "pages/masculino-servicos-laser.html", None, ()),
        ("/masculino/servicos/esfoliacao", "pages/masculino-servicos-esfoliacao.html", None, ()),
        ("/area/virilha", "pages/area-virilha.html", None, ()),
        ("/area/pernas", "pages/area-pernas.html", None, ()),
        ("/area/axilas", "pages/area-axilas.html", None, ()),
        ("/area/rosto", "pages/area-rosto.html", None, ()),
        ("/area/corpo", "pages/area-corpo.html", None, ()),
        ("/masculino/area/torax", "pages/masculino-area-torax.html", None, ()),
        ("/masculino/area/axilas", "pages/masculino-area-axilas.html", None, ()),
        ("/masculino/area/pernas", "pages/masculino-area-pernas.html", None, ()),
        ("/masculino/area/rosto", "pages/masculino-area-rosto.html", None, ()),
        ("/masculino/area/corpo", "pages/masculino-area-corpo.html", None, ()),
        ("/planos", "pages/planos.html", None, ()),
        ("/masculino/planos", "pages/masculino-planos.html", None, ()),
        ("/produtos", "pages/produtos.html", None, ()),
        ("/masculino/produtos", "pages/masculino-produtos.html", None, ()),
        ("/cartao-presente", "pages/cartao-presente.html", None, ()),
        ("/masculino/cartao-presente", "pages/masculino-cartao-presente.html", None, ()),
        ("/desejos", "pages/desejos.html", None, ()),
        ("/termos", "pages/termos.html", None, ()),
        ("/privacidade", "pages/privacidade.html", None, ()),
    ]
    ids = catalog_ids()
    for product_id in ids:
        pages.append(
            (
                f"/produto/{product_id}",
                f"products/{product_id}.html",
                None,
                product_scripts,
            )
        )
    routes = {"carrinho": "carrinho.html"}
    page_files = {}
    for path, name, title, scripts in pages:
        raw = fetch(ORIGIN + path).decode("utf-8", "replace")
        if title is None:
            match = re.search(r"<title>(.*?)</title>", raw)
            title = match.group(1) if match else "Pello Menos"
        if not css:
            css = pull_css(raw)
            (OUT / "home.css").write_text(css, encoding="utf-8")
        product_id = Path(name).stem if name.startswith("products/") else None
        document = extract_document(raw, title, scripts, product_id=product_id)
        document = unwrap_react_hidden(document)
        document = collect_and_rewrite_assets(document, copied)
        document = rewrite_links(document, slugs)
        if name in ("home.html", "masculino.html"):
            document = apply_hero_backgrounds(document)
        dest = OUT / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(document, encoding="utf-8")
        if name.startswith("products/"):
            # Catalog id always owns its route â€” never let a shared Woo slug
            # from another product (esp. *-masc / esfoliaÃ§Ã£o) overwrite it.
            routes[product_id] = name.replace("\\", "/")
        print(name, "bytes", len(document), "assets", len(copied))
        if name.startswith("pages/"):
            page_files[path] = name.replace("\\", "/")
    # Woo slug aliases only when the key is free (not already a catalog id).
    # Prefer feminine / non-esfoliaÃ§Ã£o when several products share a slug.
    claimants = {}
    for pid, info in bridge.items():
        html = routes.get(pid)
        if not html:
            continue
        slug = (info or {}).get("slug")
        if not slug or slug == pid:
            continue
        claimants.setdefault(slug, []).append(pid)

    def slug_alias_score(pid, slug):
        score = 0
        if pid == slug:
            score += 200
        if not str(pid).endswith("-masc"):
            score += 100
        if not str(pid).startswith("esfoliacao-"):
            score += 50
        return score

    for slug, pids in claimants.items():
        if slug in routes:
            continue
        best = max(pids, key=lambda pid: slug_alias_score(pid, slug))
        routes[slug] = routes[best]
    page_files["/produto-categoria/depilacao-a-cera"] = page_files["/servicos/cera"]
    page_files["/depilacao-a-cera"] = page_files["/servicos/cera"]
    page_files["/produto-categoria/depilacao-a-laser"] = page_files["/servicos/laser"]
    page_files["/depilacao-a-laser"] = page_files["/servicos/laser"]
    (OUT / "pages.json").write_text(
        json.dumps(page_files, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (OUT / "routes.json").write_text(
        json.dumps(routes, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print("routes", len(routes))
    # Imagens do "Adicione tambÃ©m" (cart-related.json) = mesma imagem da ficha:
    # garante que todo caminho do JSON exista em media/, mesmo sem aparecer em HTML.
    related_path = OUT / "cart-related.json"
    if related_path.is_file():
        related = json.loads(related_path.read_text(encoding="utf-8"))
        missing = []
        for row in (related.get("products") or {}).values():
            path = str(row.get("image") or "").split("?", 1)[0]
            if not path.startswith("/images/"):
                continue
            local = PUBLIC / path.lstrip("/")
            if not local.is_file():
                missing.append(path)
                continue
            dest = OUT / "media" / path.lstrip("/")
            dest.parent.mkdir(parents=True, exist_ok=True)
            if path not in copied:
                shutil.copy2(local, dest)
                copied.add(path)
            # mesma versÃ£o (?v=hash) que a ficha usa â†’ cart.js monta mediaBase + path.
            row["image"] = f"{path}?v={media_version(local)}"
        if missing:
            raise SystemExit(f"cart-related: imagens ausentes em public/: {missing}")
        related_path.write_text(
            json.dumps(related, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print("cart-related images ok", len(related.get("products") or {}))


def _balanced_div_blocks(html: str, opener_re: str):
    blocks = []
    for match in re.finditer(opener_re, html):
        start = match.start()
        index = match.end()
        depth = 1
        while index < len(html) and depth:
            next_open = html.find("<div", index)
            next_close = html.find("</div>", index)
            if next_close < 0:
                break
            if next_open != -1 and next_open < next_close:
                depth += 1
                index = next_open + 4
            else:
                depth -= 1
                index = next_close + len("</div>")
        blocks.append(html[start:index])
    return blocks


def unwrap_react_hidden(html: str) -> str:
    # Next/RSC marks suspended trees with hidden until hydration; without React they stay invisible.
    html = re.sub(r"<div hidden=\"\">.*?</div>", "", html, count=1, flags=re.S)
    html = re.sub(r"<div hidden( id=\"[^\"]*\")?>", r"<div\1>", html)

    blocks = _balanced_div_blocks(html, r'<div id="S:\d+">')
    if not blocks:
        return html

    for block in blocks:
        html = html.replace(block, "", 1)

    pieces = []
    for block in blocks:
        content = re.sub(r'^<div id="S:\d+">', "", block)
        content = re.sub(r"</div>\s*$", "", content)
        pieces.append(content)
    joined = "".join(pieces)

    # Replace the loading fallback inside .flex-1 with the real home markup.
    replaced = re.sub(
        r'(<div class="flex-1">).*?(</div>\s*<footer\b)',
        r"\1" + joined + r"\2",
        html,
        count=1,
        flags=re.S,
    )
    if replaced == html and "<footer" in html:
        replaced = re.sub(r"(<footer\b)", joined + r"\1", html, count=1)
    return replaced


def apply_hero_backgrounds(html: str) -> str:
    """Keep each slide's picture so desktop/tablet/mobile use their own file."""
    style = """<style>
#inicio{position:relative;overflow:hidden;width:100%;aspect-ratio:3/4}
@media (min-width:768px){#inicio{aspect-ratio:auto;height:480px}}
@media (min-width:1024px){#inicio{aspect-ratio:auto;height:min(680px,calc(100dvh - 10.5rem))}}
#inicio>[data-hero-slide]{position:absolute;inset:0}
#inicio [data-hero-slide] picture,#inicio [data-hero-slide] img{position:absolute;inset:0;display:block;width:100%;height:100%;object-fit:cover;object-position:50% 50%}
#inicio .js-hero-copy{position:relative;z-index:10;height:100%}
</style>
"""
    for css_href in (
        f'href="{ASSET_BASE}/home.css?v=premium7">',
        f'href="{ASSET_BASE}/home.css?v=premium6">',
    ):
        if css_href in html and "#inicio>[data-hero-slide]" not in html:
            html = html.replace(css_href, css_href + "\n" + style, 1)
            break
    return html


if __name__ == "__main__":
    main()
