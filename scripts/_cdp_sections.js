const { spawn } = require("child_process");
const chrome = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const port = 9336;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

async function main() {
  const proc = spawn(chrome, [`--remote-debugging-port=${port}`, "--headless=new", "--disable-gpu", "--no-first-run", "--user-data-dir=C:\\Users\\GC1\\AppData\\Local\\Temp\\pm-chrome-profile4", "about:blank"], { stdio: "ignore" });
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
    await send("Emulation.setDeviceMetricsOverride", { width: 1440, height: 900, deviceScaleFactor: 1, mobile: false });
    await send("Page.navigate", { url: "https://pellomenos.companygenesis.com.br/?nocache=cdp5" });
    await sleep(3000);
    const out = await send("Runtime.evaluate", {
      expression: `(() => {
        const slides = [...document.querySelectorAll('[data-hero-slide]')].map((el,i)=>({i, op:getComputedStyle(el).opacity, bg:getComputedStyle(el).backgroundImage.slice(0,100), cls:el.className.includes('opacity-100')}));
        const sections = [...document.querySelectorAll('section')].map(el => ({id:el.id||el.getAttribute('data-home-panel')||'', h:el.clientHeight, op:getComputedStyle(el).opacity, hidden:el.classList.contains('hidden'), y:Math.round(el.getBoundingClientRect().y+scrollY)}));
        const cards = document.querySelectorAll('[data-product-card]').length;
        const imgs = [...document.querySelectorAll('img')].slice(0,8).map(img=>({w:img.clientWidth,h:img.clientHeight,nw:img.naturalWidth,src:(img.currentSrc||img.src).split('/').pop()}));
        const hiddenParents = [...document.querySelectorAll('[hidden]')].map(el=>({tag:el.tagName, id:el.id, kids:el.children.length, text:(el.textContent||'').slice(0,40)}));
        return JSON.stringify({slides, sections:sections.slice(0,20), cards, imgs, hiddenParents:hiddenParents.slice(0,10), footerY: Math.round(document.querySelector('footer').getBoundingClientRect().y+scrollY)});
      })()`,
      returnByValue: true,
    });
    console.log(out.result.result.value);
    ws.close();
  } finally { proc.kill(); }
}
main().catch((e)=>{console.error(e);process.exit(1);});
