/**
 * Harness local para o redesign do carrinho: serve carrinho.html com as URLs
 * absolutas da loja reescritas para o servidor local, para validar layout e
 * interacoes sem publicar em producao.
 *
 * Uso: node scripts/_qa_cart_server.cjs [porta]
 */
const http = require("http");
const fs = require("fs");
const path = require("path");

const ROOT = path.resolve(__dirname, "..");
const PM = path.join(ROOT, "wordpress-loja", "pm-home");
const PORT = Number(process.argv[2] || 8899);
const PROD_ASSETS = "https://loja.pellomenos.com.br/wp-content/uploads/pm-home/";
const LOCAL_ASSETS = `http://localhost:${PORT}/wp-content/uploads/pm-home/`;

const TYPES = {
  ".html": "text/html; charset=utf-8",
  ".js": "application/javascript; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".webp": "image/webp",
  ".png": "image/png",
  ".jpg": "image/jpeg",
  ".svg": "image/svg+xml",
  ".woff2": "font/woff2",
};

http
  .createServer((req, res) => {
    const url = new URL(req.url, `http://localhost:${PORT}`);
    let p = decodeURIComponent(url.pathname);

    if (p === "/" || p === "/carrinho" || p === "/carrinho/") {
      let html = fs.readFileSync(path.join(PM, "carrinho.html"), "utf8");
      html = html.split(PROD_ASSETS).join(LOCAL_ASSETS);
      res.writeHead(200, { "Content-Type": TYPES[".html"], "Cache-Control": "no-store" });
      return res.end(html);
    }

    const prefix = "/wp-content/uploads/pm-home/";
    if (p.startsWith(prefix)) {
      p = p.slice(prefix.length);
    }
    const file = path.join(PM, p.replace(/^\/+/, ""));
    if (!file.startsWith(PM) || !fs.existsSync(file) || fs.statSync(file).isDirectory()) {
      res.writeHead(404, { "Content-Type": "text/plain" });
      return res.end("nao encontrado");
    }
    res.writeHead(200, {
      "Content-Type": TYPES[path.extname(file)] || "application/octet-stream",
      "Cache-Control": "no-store",
    });
    fs.createReadStream(file).pipe(res);
  })
  .listen(PORT, () => console.log(`harness em http://localhost:${PORT}/carrinho/`));
