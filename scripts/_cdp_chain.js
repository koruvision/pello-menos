const { spawn } = require("child_process");
const fs = require("fs");
const chrome = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const port = 9334;

function sleep(ms) {
  return new Promise((r) => setTimeout(r, ms));
}

async function waitPort() {
  for (let i = 0; i < 40; i++) {
    try {
      if ((await fetch(`http://127.0.0.1:${port}/json/version`)).ok) return;
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
      "--user-data-dir=C:\\Users\\GC1\\AppData\\Local\\Temp\\pm-chrome-profile2",
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
      url: "https://pellomenos.companygenesis.com.br/?nocache=cdp3",
    });
    await sleep(7000);
    const out = await send("Runtime.evaluate", {
      expression: `(() => {
        function info(el) {
          if (!el) return null;
          const r = el.getBoundingClientRect();
          const s = getComputedStyle(el);
          return {
            tag: el.tagName,
            cls: (el.className||'').toString().slice(0,80),
            w: Math.round(r.width),
            h: Math.round(r.height),
            display: s.display,
            overflow: s.overflow,
            transform: s.transform,
          };
        }
        const s = document.querySelector('#inicio');
        const chain = [];
        let n = s;
        while (n) {
          chain.push(info(n));
          n = n.parentElement;
        }
        return JSON.stringify({
          vw: innerWidth,
          body: info(document.body),
          chain,
          header: info(document.querySelector('header')),
        });
      })()`,
      returnByValue: true,
    });
    console.log(out.result.result.value);
    const shot = await send("Page.captureScreenshot", { format: "png" });
    fs.writeFileSync(
      "C:\\\\Users\\\\GC1\\\\AppData\\\\Local\\\\Temp\\\\pm-shot\\\\cdp.png",
      Buffer.from(shot.result.data, "base64"),
    );
    console.log("shot ok");
    ws.close();
  } finally {
    proc.kill();
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
