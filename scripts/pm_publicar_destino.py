# -*- coding: utf-8 -*-
"""Publica o front do projeto num WordPress de destino, um recorte por vez.

Uso (PowerShell):
  python scripts/pm_publicar_destino.py --env projeto-migracao/.secrets/oficialteste.env plugin
  python scripts/pm_publicar_destino.py --env ... snippet --routes ""          # só a rota REST do bundle
  python scripts/pm_publicar_destino.py --env ... bundle                       # sobe pm-home com a base do destino
  python scripts/pm_publicar_destino.py --env ... snippet --routes home        # fase 1
  python scripts/pm_publicar_destino.py --env ... snippet --routes home,masculino,produto
  python scripts/pm_publicar_destino.py --env ... snippet --off                # volta atrás: desativa o snippet
  python scripts/pm_publicar_destino.py --env ... snippet --all                # tudo, como no clone

O arquivo .env precisa de PM_OFICIALTESTE_URL, PM_OFICIALTESTE_USER e PM_OFICIALTESTE_APP_PASSWORD
(ou as mesmas chaves com outro prefixo, passando --prefix).

Nunca aponta para loja.pellomenos.com.br sem --permitir-loja.
"""
import argparse
import base64
import io
import json
import sys
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PM_HOME = ROOT / "wordpress-loja" / "pm-home"
SNIPPET_PHP = ROOT / "scripts" / "pm_home_snippet.php"
CLONE_BASE = "https://pellomenos.companygenesis.com.br/wp-content/uploads/pm-home"
TEXT_SUFFIXES = {".html", ".js", ".css", ".json", ".php", ".txt", ".svg"}
SNIPPET_NAME = "pm-home (front do projeto)"


def read_env(path, prefix):
    values = {}
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    try:
        return {
            "url": values[f"{prefix}_URL"].rstrip("/"),
            "user": values[f"{prefix}_USER"],
            "password": values[f"{prefix}_APP_PASSWORD"],
        }
    except KeyError as error:
        sys.exit(f"falta {error} em {path}")


class Site:
    def __init__(self, cfg):
        self.base = cfg["url"]
        self.token = base64.b64encode(f"{cfg['user']}:{cfg['password']}".encode()).decode()
        self.state_path = Path(cfg["state"])

    def call(self, method, path, payload=None, raw=None, content_type="application/json", timeout=120):
        data = raw if raw is not None else (None if payload is None else json.dumps(payload).encode("utf-8"))
        request = urllib.request.Request(
            self.base + path,
            data=data,
            method=method,
            headers={
                "User-Agent": "Mozilla/5.0 (compatible; pm-publicar/1.0)",
                "Authorization": "Basic " + self.token,
                "Content-Type": content_type,
                "Accept": "application/json",
                "Cache-Control": "no-cache",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                body = response.read().decode("utf-8", "replace")
                return response.status, (json.loads(body) if body[:1] in "[{" else body)
        except urllib.error.HTTPError as error:
            body = error.read().decode("utf-8", "replace")
            return error.code, (json.loads(body) if body[:1] in "[{" else body[:600])

    def state(self):
        if self.state_path.exists():
            return json.loads(self.state_path.read_text(encoding="utf-8"))
        return {}

    def save_state(self, data):
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        self.state_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def cmd_plugin(site, args):
    slug = "code-snippets/code-snippets"
    status, current = site.call("GET", f"/wp-json/wp/v2/plugins/{slug}")
    print("antes:", status, current.get("status") if isinstance(current, dict) else current)
    if isinstance(current, dict) and current.get("status") == "active":
        return
    status, updated = site.call("POST", f"/wp-json/wp/v2/plugins/{slug}", {"status": "active"})
    print("depois:", status, updated.get("status") if isinstance(updated, dict) else updated)
    status, probe = site.call("GET", "/wp-json/code-snippets/v1/snippets")
    print("code-snippets/v1:", status, (len(probe) if isinstance(probe, list) else probe))


def build_zip(dest_base):
    buffer = io.BytesIO()
    replaced = 0
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(PM_HOME.rglob("*")):
            if not path.is_file():
                continue
            name = path.relative_to(PM_HOME).as_posix()
            if path.suffix.lower() in TEXT_SUFFIXES:
                text = path.read_text(encoding="utf-8")
                if CLONE_BASE in text:
                    replaced += text.count(CLONE_BASE)
                    text = text.replace(CLONE_BASE, dest_base)
                archive.writestr(name, text.encode("utf-8"))
            else:
                archive.write(path, name)
    return buffer.getvalue(), replaced


def cmd_bundle(site, args):
    dest_base = site.base + "/wp-content/uploads/pm-home"
    blob, replaced = build_zip(dest_base)
    print(f"zip {len(blob)} bytes, {replaced} referências reescritas para {dest_base}")
    status, result = site.call("POST", "/wp-json/pm-home/v1/bundle", raw=blob, content_type="application/zip", timeout=1800)
    print("bundle:", status, result)
    if status != 200:
        sys.exit(1)
    for probe in ("/wp-content/uploads/pm-home/home.html", "/wp-content/uploads/pm-home/home.css"):
        status, body = site.call("GET", probe + "?v=probe")
        print(probe, status, len(body) if isinstance(body, str) else body)


def snippet_code(routes, everything):
    code = SNIPPET_PHP.read_text(encoding="utf-8")
    if everything:
        return code
    return f"define('PM_HOME_ROUTES', '{routes}');\n\n" + code


def cmd_snippet(site, args):
    state = site.state()
    snippet_id = args.id or state.get("snippet_id")
    if snippet_id is None:
        status, rows = site.call("GET", "/wp-json/code-snippets/v1/snippets")
        if status != 200:
            sys.exit(f"code-snippets/v1 respondeu {status}: {rows}")
        for row in rows:
            if row.get("name") == SNIPPET_NAME:
                snippet_id = row.get("id")
    if args.off:
        if snippet_id is None:
            print("nenhum snippet para desativar")
            return
        status, saved = site.call("PUT", f"/wp-json/code-snippets/v1/snippets/{snippet_id}", {"active": False})
        print("desativado:", status, saved.get("active") if isinstance(saved, dict) else saved)
        state.update({"snippet_id": snippet_id, "routes": None, "active": False})
        site.save_state(state)
        return
    code = snippet_code(args.routes or "", args.all)
    current = {}
    if snippet_id is not None:
        status, current = site.call("GET", f"/wp-json/code-snippets/v1/snippets/{snippet_id}")
        if status != 200 or not isinstance(current, dict):
            sys.exit(f"snippet {snippet_id} não lido: {status} {current}")
    # Code Snippets REST no oficialteste rejeita alguns campos extras com 403;
    # name/code/scope/active bastam (conferido no PUT do shell c10).
    payload = {
        "name": current.get("name") or SNIPPET_NAME,
        "code": code,
        "scope": current.get("scope") or "global",
        "active": True,
    }
    if snippet_id is None:
        status, saved = site.call("POST", "/wp-json/code-snippets/v1/snippets", payload)
    else:
        status, saved = site.call("PUT", f"/wp-json/code-snippets/v1/snippets/{snippet_id}", payload)
    if status not in (200, 201) or not isinstance(saved, dict):
        sys.exit(f"snippet falhou: {status} {saved}")
    snippet_id = saved.get("id", snippet_id)
    saved_code = saved.get("code") or ""
    print(
        "snippet", snippet_id, "ativo", saved.get("active"),
        "rotas", ("todas" if args.all else args.routes or "(nenhuma)"),
        "len", len(saved_code),
    )
    state.update({"snippet_id": snippet_id, "routes": ("ALL" if args.all else args.routes or ""), "active": True})
    site.save_state(state)
    status, probe = site.call("POST", "/wp-json/pm-home/v1/bundle", raw=b"x", content_type="application/zip")
    print("pm-home/v1/bundle existe:", status == 400, f"(HTTP {status}, esperado 400 pm_empty)")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--env", required=True)
    parser.add_argument("--prefix", default="PM_OFICIALTESTE")
    parser.add_argument("--permitir-loja", action="store_true")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("plugin")
    sub.add_parser("bundle")
    snippet = sub.add_parser("snippet")
    snippet.add_argument("--routes", default="")
    snippet.add_argument("--all", action="store_true")
    snippet.add_argument("--off", action="store_true")
    snippet.add_argument("--id", type=int, default=0, help="atualiza este id em vez de procurar pelo nome")
    args = parser.parse_args()

    cfg = read_env(args.env, args.prefix)
    if "loja.pellomenos.com.br" in cfg["url"] and not args.permitir_loja:
        sys.exit("destino é a loja oficial; pare e peça GO explícito (--permitir-loja)")
    cfg["state"] = str(Path(args.env).resolve().parent / f"{Path(args.env).stem}.state.json")
    site = Site(cfg)
    print("destino:", site.base)
    {"plugin": cmd_plugin, "bundle": cmd_bundle, "snippet": cmd_snippet}[args.command](site, args)


if __name__ == "__main__":
    main()
