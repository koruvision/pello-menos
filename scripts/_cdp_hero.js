const chrome = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const { spawn } = require("child_process");

const proc = spawn(chrome, [
  "--headless=new",
  "--disable-gpu",
  "--remote-debugging-port=9223",
  "--window-size=1440,1600",
  "about:blank",
], { stdio: "ignore" });

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function main() {
  let tabs;
  for (let i = 0; i < 20; i++) {
    try {
      const res = await fetch("http://127.0.0.1:9223/json/list");
      tabs = await res.json();
      if (tabs.length) break;
    } catch (error) {
      await sleep(250);
    }
  }
  const page = tabs.find((tab) => tab.type === "page");
  const ws = new WebSocket(page.webSocketDebuggerUrl);
  let id = 0;
  const pending = new Map();
  ws.addEventListener("message", (event) => {
    const data = JSON.parse(event.data);
    if (data.id && pending.has(data.id)) {
      pending.get(data.id)(data);
      pending.delete(data.id);
    }
  });
  function send(method, params) {
    const next = ++id;
    ws.send(JSON.stringify({ id: next, method, params }));
    return new Promise((resolve) => pending.set(next, resolve));
  }
  await new Promise((resolve) => ws.addEventListener("open", resolve));
  await send("Page.enable");
  await send("Emulation.setDeviceMetricsOverride", {
    width: 1440,
    height: 1600,
    deviceScaleFactor: 1,
    mobile: false,
  });
  await send("Page.navigate", {
    url: "https://pellomenos.companygenesis.com.br/?nocache=cdp1",
  });
  await sleep(5000);
  const result = await send("Runtime.evaluate", {
    expression: `(() => {
      const img = document.querySelector('#inicio img');
      const h1 = document.querySelector('#inicio h1');
      const slide = document.querySelector('[data-hero-slide="0"]');
      const section = document.querySelector('#inicio');
      const box = (node) => {
        if (!node) return null;
        const r = node.getBoundingClientRect();
        const s = getComputedStyle(node);
        return { w: Math.round(r.width), h: Math.round(r.height), y: Math.round(r.y), top: s.top, left: s.left, bottom: s.bottom, right: s.right, pos: s.position, hcss: s.height };
      };
      return JSON.stringify({ img: box(img), h1: box(h1), slide: box(slide), section: box(section), natural: img && img.naturalWidth, vw: innerWidth, vh: innerHeight });
    })()`,
    returnByValue: true,
  });
  console.log(result.result.result.value);
  ws.close();
  proc.kill();
}

main().catch((error) => {
  console.error(error);
  proc.kill();
  process.exit(1);
});
