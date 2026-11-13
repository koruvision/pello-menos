const { spawn } = require("child_process");
const fs = require("fs");
const chrome = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const port = 9335;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

async function main() {
  const proc = spawn(chrome, [`--remote-debugging-port=${port}`, "--headless=new", "--disable-gpu", "--no-first-run", "--user-data-dir=C:\\Users\\GC1\\AppData\\Local\\Temp\\pm-chrome-profile3", "about:blank"], { stdio: "ignore" });
  try {
    for (let i = 0; i < 40; i++) {
      try { if ((await fetch(`http://127.0.0.1:${port}/json/version`)).ok) break; } catch (_) {}
      await sleep(200);
    }
    const tabs = await (await fetch(`http://127.0.0.1:${port}/json/list`)).json();
    const page = tabs.find((t) => t.type === "page") || tabs[0];
    const ws = new WebSocket(page.webSocketDebuggerUrl);
    let id = 0; const pending = new Map();
    ws.addEventListener("message", (ev) => { const m = JSON.parse(ev.data); if (m.id && pending.has(m.id)) { pending.get(m.id)(m); pending.delete(m.id); } });
    await new Promise((r) => ws.addEventListener("open", r));
    const send = (method, params = {}) => { const n = ++id; ws.send(JSON.stringify({ id: n, method, params })); return new Promise((r) => pending.set(n, r)); };
    await send("Page.enable");
    await send("Network.enable");
    await send("Emulation.setDeviceMetricsOverride", { width: 1440, height: 900, deviceScaleFactor: 1, mobile: false });
    const failed = [];
    ws.addEventListener("message", (ev) => {
      const m = JSON.parse(ev.data);
      if (m.method === "Network.loadingFailed") failed.push(m.params);
    });
    await send("Page.navigate", { url: "https://pellomenos.companygenesis.com.br/?nocache=cdp4" });
    await sleep(8000);
    const out = await send("Runtime.evaluate", {
      expression: `(() => {
        const slide = document.querySelector('[data-hero-slide="0"]');
        const s = getComputedStyle(slide);
        const h1 = document.querySelector('#inicio h1');
        return JSON.stringify({
          slide: { w: slide.clientWidth, h: slide.clientHeight, op: s.opacity, bg: s.backgroundImage, size: s.backgroundSize, pos: s.backgroundPosition, z: s.zIndex },
          h1: h1 ? { text: h1.textContent, w: h1.clientWidth, h: h1.clientHeight, color: getComputedStyle(h1).color, op: getComputedStyle(h1).opacity } : null,
          slides: [...document.querySelectorAll('[data-hero-slide]')].map(el => ({ op: getComputedStyle(el).opacity, cls: el.className })),
        });
      })()`,
      returnByValue: true,
    });
    console.log(out.result.result.value);
    console.log("failed", JSON.stringify(failed.slice(0, 5)));
    const shot = await send("Page.captureScreenshot", { format: "png", captureBeyondViewport: true });
    fs.writeFileSync("C:\\\\Users\\\\GC1\\\\AppData\\\\Local\\\\Temp\\\\pm-shot\\\\full.png", Buffer.from(shot.result.data, "base64"));
    console.log("full shot", Buffer.from(shot.result.data, "base64").length);
    ws.close();
  } finally { proc.kill(); }
}
main().catch((e) => { console.error(e); process.exit(1); });
