const { spawn } = require("child_process");
const chrome = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const port = 9333;

function sleep(ms) {
  return new Promise((r) => setTimeout(r, ms));
}

async function waitPort() {
  for (let i = 0; i < 40; i++) {
    try {
      const res = await fetch(`http://127.0.0.1:${port}/json/version`);
      if (res.ok) return;
    } catch (_) {}
    await sleep(200);
  }
  throw new Error("no chrome");
}

async function main() {
  const proc = spawn(
    chrome,
    [
      `--remote-debugging-port=${port}`,
      "--headless=new",
      "--disable-gpu",
      "--no-first-run",
      "--user-data-dir=C:\\Users\\GC1\\AppData\\Local\\Temp\\pm-chrome-profile",
      "about:blank",
    ],
    { stdio: "ignore" },
  );
  try {
    await waitPort();
    const tabs = await (await fetch(`http://127.0.0.1:${port}/json/list`)).json();
    const page = tabs.find((t) => t.type === "page") || tabs[0];
    const ws = new WebSocket(page.webSocketDebuggerUrl);
    let id = 0;
    const pending = new Map();
    ws.addEventListener("message", (ev) => {
      const msg = JSON.parse(ev.data);
      if (msg.id && pending.has(msg.id)) {
        pending.get(msg.id)(msg);
        pending.delete(msg.id);
      }
    });
    await new Promise((resolve) => ws.addEventListener("open", resolve));
    const send = (method, params = {}) => {
      const next = ++id;
      ws.send(JSON.stringify({ id: next, method, params }));
      return new Promise((resolve) => pending.set(next, resolve));
    };
    await send("Page.enable");
    await send("Runtime.enable");
    await send("Emulation.setDeviceMetricsOverride", {
      width: 1440,
      height: 900,
      deviceScaleFactor: 1,
      mobile: false,
    });
    await send("Page.navigate", {
      url: "https://pellomenos.companygenesis.com.br/?nocache=cdp2",
    });
    await sleep(6000);
    const out = await send("Runtime.evaluate", {
      expression: `(() => {
        const s = document.querySelector('#inicio');
        const slide = document.querySelector('[data-hero-slide="0"]');
        const copy = document.querySelector('.js-hero-copy');
        const cs = getComputedStyle(s);
        const cssSlide = getComputedStyle(slide);
        return JSON.stringify({
          vw: innerWidth,
          section: { w: s.clientWidth, h: s.clientHeight, pos: cs.position, ar: cs.aspectRatio },
          slide: { w: slide.clientWidth, h: slide.clientHeight, pos: cssSlide.position, inset: cssSlide.inset, bg: cssSlide.backgroundImage.slice(0,120), size: cssSlide.backgroundSize },
          copy: { w: copy.clientWidth, h: copy.clientHeight, text: (copy.innerText||'').slice(0,80) },
        });
      })()`,
      returnByValue: true,
    });
    console.log(out.result.result.value);
    ws.close();
  } finally {
    proc.kill();
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
